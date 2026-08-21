package ils_el

import upickle.default.write

/** Black-box runner: emits the result envelope defined in spec SS 4.3.
  *
  * A plain `main` rather than `@main`: Scala 3's `@main` is meant for top-level
  * methods and synthesises an entry point named after the method, so inside an
  * object the class actually launched is not obvious. build.mill pins mainClass
  * to this object so Mill auto-detects nothing.
  */
object Main:
  def main(args: Array[String]): Unit =
    val root = os.Path(sys.env.getOrElse("CONFORMANCE_ROOT", os.pwd.toString))
    // Annotated: the two branches are an Array and an IndexedSeq, whose least
    // upper bound is not a Seq without help.
    val paths: Seq[os.Path] =
      if args.nonEmpty then args.toSeq.map(a => os.Path(a, os.pwd))
      else os.walk(root / "conformance" / "cases").filter(_.ext == "json").sorted

    val results = paths.map: p =>
      val c = Case.load(p)
      val losses = Ylt.readYlt(Case.dataPath(root, c), Some(c.input.sha256))
      ujson.Obj(
        "case" -> c.id,
        "impl" -> "scala",
        "spec_version" -> "1.0",
        "value" -> Ylt.expectedLoss(losses, c.operation.n_years)
      )

    println(write(ujson.Arr(results*), indent = 2))
