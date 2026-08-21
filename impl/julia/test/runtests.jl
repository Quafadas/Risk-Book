# Native harness over the shared corpus. Tolerances come from the case data,
# never from this file (spec § 6.2).

using ILSEL
using JSON3
using Test

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const CASES_DIR = joinpath(ROOT, "conformance", "cases")

case_paths() = sort([
    joinpath(r, f)
    for (r, _, fs) in walkdir(CASES_DIR) for f in fs if endswith(f, ".json")
])

"""Error in units in the last place, against the golden binary64."""
function ulp_error(actual::Float64, expected::Float64)
    actual == expected && return 0.0
    return abs(actual - expected) / eps(expected)
end

@testset "ILS conformance v1.0" begin
    paths = case_paths()
    @test !isempty(paths)

    for p in paths
        c = JSON3.read(read(p, String))
        @testset "$(c.id)" begin
            losses = read_ylt(
                joinpath(ROOT, "conformance", c.input.file);
                expected_sha256 = c.input.sha256,
            )
            @test length(losses) == c.input.rows

            actual = expected_loss(losses, c.operation.n_years)
            expected = parse(Float64, c.expected.binary64_hex)
            @test ulp_error(actual, expected) <= c.tolerance.compensated.ulp
        end
    end

    @testset "naive left fold is rejected" begin
        c = JSON3.read(read(joinpath(CASES_DIR, "el", "mean-ylt-10k.json"), String))
        losses = read_ylt(joinpath(ROOT, "conformance", c.input.file))
        expected = parse(Float64, c.expected.binary64_hex)
        naive = 0.0
        for x in losses
            naive += x
        end
        # If this ever fails, the case has stopped discriminating between
        # summation strategies and needs strengthening, not deleting.
        @test ulp_error(naive / c.operation.n_years, expected) > 1.0
    end

    @testset "pairwise sum happens to agree here" begin
        # Documents the coincidence noted in ILSEL.compensated_sum: Base.sum is
        # pairwise and lands on the golden value for this input. Conformance
        # still requires § 3.2 -- this is an observation, not a licence.
        c = JSON3.read(read(joinpath(CASES_DIR, "el", "mean-ylt-10k.json"), String))
        losses = read_ylt(joinpath(ROOT, "conformance", c.input.file))
        expected = parse(Float64, c.expected.binary64_hex)
        @test ulp_error(sum(losses) / c.operation.n_years, expected) == 0.0
    end

    @testset "compensated sum survives a dominant year" begin
        @test compensated_sum([1.0, 1e100, 1.0, -1e100]) == 2.0
    end

    @testset "digest mismatch is fatal" begin
        tmp = tempname() * ".csv"
        write(tmp, "year,loss\n1,1.00\n")
        @test_throws ErrorException read_ylt(tmp; expected_sha256 = "0"^64)
    end
end
