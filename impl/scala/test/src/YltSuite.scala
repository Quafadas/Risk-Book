package ils_el

/** Native harness over the shared corpus. Tolerances come from the case data,
  * never from this file (spec SS 4.1).
  */
class YltSuite extends munit.FunSuite:

  private val root = os.Path(sys.env.getOrElse(
    "CONFORMANCE_ROOT",
    throw new IllegalStateException("CONFORMANCE_ROOT is unset")
  ))
  private val casesDir = root / "conformance" / "cases"

  private val cases: Seq[os.Path] =
    os.walk(casesDir).filter(_.ext == "json").sorted

  test("corpus is non-empty"):
    assert(cases.nonEmpty, s"no cases found under $casesDir")

  cases.foreach: p =>
    val c = Case.load(p)
    val expected = Case.golden(c)

    test(s"${c.id}: expected loss"):
      val losses = Ylt.readYlt(Case.dataPath(root, c), Some(c.input.sha256))
      assertEquals(losses.length, c.input.rows)
      val actual = Ylt.expectedLoss(losses, c.operation.n_years)
      val err = Case.relativeError(actual, expected)
      assert(
        err <= c.tolerance.rel,
        s"${c.id}: got $actual, want $expected ($err relative, tolerance ${c.tolerance.rel})"
      )

    test(s"${c.id}: tolerance catches a real error"):
      // Dropping one loss-bearing year is the cheapest realistic mistake, an
      // off-by-one on the row range. It must fail (spec SS 4.1).
      val losses = Ylt.readYlt(Case.dataPath(root, c))
      val smallest = losses.filter(_ > 0.0).min
      val dropped = losses.patch(losses.indexOf(smallest), Nil, 1)
      val actual = Ylt.expectedLoss(dropped, c.operation.n_years)
      assert(
        Case.relativeError(actual, expected) > c.tolerance.rel,
        "dropping a loss-bearing year still passes; the tolerance is too wide"
      )

  test("n_years must be positive"):
    intercept[IllegalArgumentException](Ylt.expectedLoss(Array(1.0, 2.0), 0))

  test("digest mismatch is fatal"):
    val tmp = os.temp("year,loss\n1,1.00\n", suffix = ".csv")
    intercept[IllegalArgumentException](Ylt.readYlt(tmp, Some("0" * 64)))
