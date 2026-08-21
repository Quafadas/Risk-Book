"""
    ILSEL

Julia implementation of the ILS risk conformance spec, v1.0.

"""
module ILSEL

using DelimitedFiles: readdlm
using SHA: sha256

export expected_loss, read_ylt

const SPEC_VERSION = v"1.0.0"

"""
    expected_loss(losses, n_years = length(losses)) -> Float64

Expected annual loss (spec § 3.1).

`Base.sum` is the array reduction -- Julia needs no array library, so this is
already the idiomatic equivalent of NumPy's `sum`. It happens to be pairwise and
exact on the v1.0 corpus; the case tolerance does not require that.
"""
function expected_loss(losses, n_years::Integer = length(losses))::Float64
    n_years > 0 || throw(ArgumentError("n_years must be positive"))
    return sum(losses) / n_years
end

"""
    read_ylt(path; expected_sha256 = nothing) -> Vector{Float64}

Read the loss column of a YLT, verifying the digest when one is supplied.

The column is located by name from the header rather than by position, so a
corpus file that grows a column does not silently shift the reading.
"""
function read_ylt(path::AbstractString; expected_sha256::Union{Nothing,AbstractString} = nothing)
    raw = read(path)
    if expected_sha256 !== nothing
        got = bytes2hex(sha256(raw))
        got == expected_sha256 || error(
            "digest mismatch for $(basename(path)): expected " *
            "$(first(expected_sha256, 16))..., got $(first(got, 16))...",
        )
    end

    data, header = readdlm(IOBuffer(raw), ','; header = true)
    names = strip.(string.(vec(header)))
    col = findfirst(==("loss"), names)
    col === nothing && error("YLT has no 'loss' column: $(names)")

    return Float64.(data[:, col])
end

end # module
