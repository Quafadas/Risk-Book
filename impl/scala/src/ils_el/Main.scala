package ils_el

import upickle.default.write

/** Black-box runner: emits the result envelope defined in spec SS 6.3. */
object Main:
  @main def run(args: String*): Unit =
    val root = os.Path(sys.env.getOrElse("CONFORMANCE_ROOT", os.pwd.toString))
    val paths =
      if args.nonEmpty then args.map(a => os.Path(a, os.pwd))
      else os.walk(root / "conformance" / "cases").filter(_.ext == "json").sorted

    val results = paths.map: p =>
      val c = Case.load(p)
      val losses = Ylt.readYlt(root / "conformance" / c.input.file, Some(c.input.sha256))
      val v = Ylt.expectedLoss(losses, c.operation.n_years)
      ujson.Obj(
        "case" -> c.id,
        "impl" -> "scala",
        "spec_version" -> "1.0",
        "value" -> v,
        "binary64_hex" -> java.lang.Double.toHexString(v)
      )

    println(write(ujson.Arr(results*), indent = 2))
