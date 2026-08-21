package ils_el

import upickle.default.{ReadWriter, macroRW, read}

/** Case-file model (spec SS 6.1). Only the fields the harness needs. */
final case class Input(kind: String, file: String, sha256: String, rows: Int)
    derives ReadWriter

final case class Operation(name: String, n_years: Int) derives ReadWriter

final case class Expected(
    exact_decimal: String,
    binary64_hex: String,
    binary64_repr: String
) derives ReadWriter

final case class UlpBudget(ulp: Double) derives ReadWriter

final case class Tolerance(compensated: UlpBudget) derives ReadWriter

final case class Case(
    id: String,
    spec: String,
    rationale: String,
    input: Input,
    operation: Operation,
    expected: Expected,
    tolerance: Tolerance
) derives ReadWriter

object Case:
  def load(p: os.Path): Case = read[Case](os.read(p))

  /** Error in units in the last place, against the golden binary64. */
  def ulpError(actual: Double, expected: Double): Double =
    if actual == expected then 0.0
    else math.abs(actual - expected) / math.ulp(expected)
