"""
    ILSEL

Julia implementation of the ILS risk conformance spec, v1.0.

Independent of `impl/python`: shares only the case corpus (spec § 6.2).
"""
module ILSEL

using SHA: sha256

export expected_loss, read_ylt

const SPEC_VERSION = v"1.0.0"

"""
    expected_loss(losses, n_years = length(losses)) -> Float64

Expected annual loss (spec § 4.1).

The sum is `Base.sum` -- the standard facility, per § 3.2. Julia's is pairwise,
so it will not match a left fold to the last bit; the case tolerance covers that.
"""
function expected_loss(losses, n_years::Integer = length(losses))::Float64
    n_years > 0 || throw(ArgumentError("n_years must be positive"))
    return sum(losses) / n_years
end

"""
    read_ylt(path; expected_sha256 = nothing) -> Vector{Float64}

Read a two-column YLT, verifying the digest when one is supplied.
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

    lines = split(String(raw), '\n'; keepempty = false)
    header = strip.(split(lines[1], ','))
    col = findfirst(==("loss"), header)
    col === nothing && error("YLT has no 'loss' column")

    return [parse(Float64, strip(split(l, ',')[col])) for l in lines[2:end]]
end

end # module
