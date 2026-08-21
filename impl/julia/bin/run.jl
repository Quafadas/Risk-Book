#!/usr/bin/env julia
# Black-box runner: emits the result envelope defined in spec § 6.3.

using ILSEL
using JSON3
using Printf

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))

paths = isempty(ARGS) ? sort([
    joinpath(r, f)
    for (r, _, fs) in walkdir(joinpath(ROOT, "conformance", "cases"))
    for f in fs if endswith(f, ".json")
]) : ARGS

results = map(paths) do p
    c = JSON3.read(read(p, String))
    losses = read_ylt(joinpath(ROOT, "conformance", c.input.file);
                      expected_sha256 = c.input.sha256)
    v = expected_loss(losses, c.operation.n_years)
    Dict(
        "case" => c.id,
        "impl" => "julia",
        "spec_version" => "1.0",
        "value" => v,
        "binary64_hex" => @sprintf("%a", v),
    )
end

JSON3.pretty(stdout, results)
println()
