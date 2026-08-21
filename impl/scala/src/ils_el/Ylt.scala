package ils_el

import java.security.MessageDigest
import vecxt.all.sumSIMD

/** Expected loss over a year loss table (spec SS 3.1). */
object Ylt:

  def expectedLoss(losses: Array[Double], nYears: Int): Double =
    require(nYears > 0, "nYears must be positive")
    losses.sumSIMD / nYears

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
    lines.tail.filter(_.nonEmpty).map(l => l.split(',')(lossCol).trim.toDouble)
