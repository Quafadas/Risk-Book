package ils_el

import upickle.default.{ReadWriter, read}

/** Case-file model (spec SS 6.1). Only the fields the harness needs. */
final case class Input(kind: String, file: String, sha256: String, rows: Int)
    derives ReadWriter

final case class Operation(name: String, n_years: Int) derives ReadWriter

final case class Expected(exact_decimal: String) derives ReadWriter

final case class Tolerance(rel: Double) derives ReadWriter

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

  /** The golden value, parsed from its decimal text (spec SS 6.1). */
  def golden(c: Case): Double = c.expected.exact_decimal.toDouble

  /** Resolve a case's input file against the corpus root.
    *
    * `input.file` is a relative path with '/' separators. os-lib rejects a
    * dynamic string containing a separator as a single path segment, so it has
    * to be parsed into segments rather than appended -- hence os.SubPath.
    */
  def dataPath(root: os.Path, c: Case): os.Path =
    root / "conformance" / os.SubPath(c.input.file)

  def relativeError(actual: Double, expected: Double): Double =
    math.abs(actual - expected) / math.abs(expected)
