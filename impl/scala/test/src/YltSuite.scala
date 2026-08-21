package ils_el

/** Native harness over the shared corpus. Tolerances come from the case data,
  * never from this file (spec SS 6.2).
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

    test(s"${c.id}: expected loss"):
      val losses = Ylt.readYlt(root / "conformance" / c.input.file, Some(c.input.sha256))
      assertEquals(losses.length, c.input.rows)
      val actual = Ylt.expectedLoss(losses, c.operation.n_years)
      val expected = java.lang.Double.parseDouble(c.expected.binary64_hex)
      val err = Case.ulpError(actual, expected)
      assert(
        err <= c.tolerance.compensated.ulp,
        s"${c.id}: got ${java.lang.Double.toHexString(actual)}, " +
          s"want ${c.expected.binary64_hex} (${err} ulp)"
      )

  test("naive left fold is rejected"):
    val c = Case.load(casesDir / "el" / "mean-ylt-10k.json")
    val losses = Ylt.readYlt(root / "conformance" / c.input.file)
    val expected = java.lang.Double.parseDouble(c.expected.binary64_hex)
    // Array.sum -- the obvious implementation, and the wrong one.
    val naive = losses.sum / c.operation.n_years
    assert(
      Case.ulpError(naive, expected) > 1.0,
      "Array.sum now agrees with the golden value; the case has stopped " +
        "discriminating between summation strategies and needs strengthening."
    )

  test("compensated sum survives a dominant year"):
    assertEquals(Ylt.compensatedSum(Array(1.0, 1e100, 1.0, -1e100)), 2.0)

  test("digest mismatch is fatal"):
    val tmp = os.temp("year,loss\n1,1.00\n", suffix = ".csv")
    intercept[IllegalArgumentException](Ylt.readYlt(tmp, Some("0" * 64)))
