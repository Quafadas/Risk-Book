package ils_el

import java.security.MessageDigest

/** Expected loss over a year loss table (spec SS 3.2, SS 4.1). */
object Ylt:

  /** Neumaier compensated summation (spec SS 3.2).
    *
    * Note the explicit loop. `Array[Double].sum` delegates to a left fold,
    * whose error grows with n -- on the 10k reference YLT it lands ~13 ulp
    * from the exact mean and fails conformance. See YltSuite.
    */
  def compensatedSum(xs: Array[Double]): Double =
    var total = 0.0
    var comp = 0.0
    var i = 0
    while i < xs.length do
      val x = xs(i)
      val t = total + x
      comp +=
        (if math.abs(total) >= math.abs(x) then (total - t) + x
         else (x - t) + total)
      total = t
      i += 1
    total + comp

  /** Expected annual loss (spec SS 4.1). */
  def expectedLoss(losses: Array[Double], nYears: Int): Double =
    require(nYears > 0, "nYears must be positive")
    compensatedSum(losses) / nYears

  def expectedLoss(losses: Array[Double]): Double =
    expectedLoss(losses, losses.length)

  /** Reads a two-column YLT, verifying the digest when one is supplied. */
  def readYlt(path: os.Path, expectedSha256: Option[String] = None): Array[Double] =
    val raw = os.read.bytes(path)
    expectedSha256.foreach: want =>
      val got = MessageDigest
        .getInstance("SHA-256")
        .digest(raw)
        .map(b => f"${b & 0xff}%02x")
        .mkString
      require(
        got == want,
        s"digest mismatch for ${path.last}: expected ${want.take(16)}..., got ${got.take(16)}..."
      )

    val lines = new String(raw, "UTF-8").linesIterator.toArray
    val header = lines.head.split(',').map(_.trim)
    val lossCol = header.indexOf("loss")
    require(lossCol >= 0, "YLT has no 'loss' column")
    lines.tail.filter(_.nonEmpty).map(l => l.split(',')(lossCol).toDouble)
