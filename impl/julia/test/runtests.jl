# Native harness over the shared corpus. Tolerances come from the case data,
# never from this file (spec § 4.1).

using ILSEL
using JSON3
using Test

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const CASES_DIR = joinpath(ROOT, "conformance", "cases")

case_paths() = sort([
    joinpath(r, f)
    for (r, _, fs) in walkdir(CASES_DIR) for f in fs if endswith(f, ".json")
])

relative_error(actual, expected) = abs(actual - expected) / abs(expected)

@testset "ILS conformance v1.0" begin
    paths = case_paths()
    @test !isempty(paths)

    for p in paths
        c = JSON3.read(read(p, String))
        expected = parse(Float64, c.expected.exact_decimal)

        @testset "$(c.id)" begin
            losses = read_ylt(
                joinpath(ROOT, "conformance", c.input.file);
                expected_sha256 = c.input.sha256,
            )
            @test length(losses) == c.input.rows

            actual = expected_loss(losses, c.operation.n_years)
            @test relative_error(actual, expected) <= c.tolerance.rel
        end

        @testset "$(c.id): tolerance catches a real error" begin
            # Dropping one loss-bearing year is the cheapest realistic mistake,
            # an off-by-one on the row range. It must fail (spec § 4.1).
            losses = read_ylt(joinpath(ROOT, "conformance", c.input.file))
            smallest = minimum(filter(>(0.0), losses))
            dropped = deleteat!(copy(losses), findfirst(==(smallest), losses))
            actual = expected_loss(dropped, c.operation.n_years)
            @test relative_error(actual, expected) > c.tolerance.rel
        end
    end

    @testset "n_years must be positive" begin
        @test_throws ArgumentError expected_loss([1.0, 2.0], 0)
    end

    @testset "digest mismatch is fatal" begin
        tmp = tempname() * ".csv"
        write(tmp, "year,loss\n1,1.00\n")
        @test_throws ErrorException read_ylt(tmp; expected_sha256 = "0"^64)
    end
end
