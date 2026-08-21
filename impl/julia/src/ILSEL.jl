"""
    ILSEL

Julia implementation of the ILS risk conformance spec, v1.0.

Independent of `impl/python`: shares only the case corpus (spec § 6.2).
"""
module ILSEL

using SHA: sha256

export compensated_sum, expected_loss, read_ylt

const SPEC_VERSION = v"1.0.0"

"""
    compensated_sum(xs) -> Float64

Neumaier compensated summation (spec § 3.2).

Written out rather than delegating to `Base.sum`. Julia's `sum` uses pairwise
summation and happens to agree with the golden value on the reference YLT, but
agreement by coincidence is not conformance: an implementation must be correct
because it follows § 3.2, not because its standard library was well chosen.
"""
function compensated_sum(xs)::Float64
    total = 0.0
    comp = 0.0
    @inbounds for x in xs
        xf = Float64(x)
        t = total + xf
        comp += ifelse(abs(total) >= abs(xf), (total - t) + xf, (xf - t) + total)
        total = t
    end
    return total + comp
end

"""
    expected_loss(losses, n_years = length(losses)) -> Float64

Expected annual loss (spec § 4.1).
"""
function expected_loss(losses, n_years::Integer = length(losses))::Float64
    n_years > 0 || throw(ArgumentError("n_years must be positive"))
    return compensated_sum(losses) / n_years
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

    return [parse(Float64, split(l, ',')[col]) for l in lines[2:end]]
end

end # module
