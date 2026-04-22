"""Tests for the allocator."""

import pytest

from rate_allocator import allocate, Institution, Tier


@pytest.fixture
def sample_institutions():
    return [
        Institution(
            name="Nu",
            tiers=(
                Tier(limit=25_000, rate=0.15),
                Tier(limit=250_000, rate=0.12),
                Tier(limit=float("inf"), rate=0.10),
            ),
        ),
        Institution(
            name="Mercado Pago",
            tiers=(
                Tier(limit=23_000, rate=0.14),
                Tier(limit=float("inf"), rate=0.10),
            ),
        ),
    ]


class TestAllocate:
    def test_allocates_full_amount(self, sample_institutions):
        result = allocate(total=100_000, institutions=sample_institutions)
        assert abs(result.total_allocated - 100_000) < 1e-6

    def test_prioritizes_higher_rates(self, sample_institutions):
        result = allocate(total=48_000, institutions=sample_institutions)
        nu_alloc = sum(result.allocations["Nu"])
        mp_alloc = sum(result.allocations["Mercado Pago"])
        assert nu_alloc == 25_000
        assert mp_alloc == 23_000

    def test_fills_tiers_sequentially(self, sample_institutions):
        result = allocate(total=50_000, institutions=sample_institutions)
        nu_alloc = result.allocations["Nu"]
        mp_alloc = result.allocations["Mercado Pago"]
        assert nu_alloc[0] == 25_000  # Nu first tier full
        mp_first = mp_alloc[0]
        assert mp_first == 23_000  # MP first tier full (higher rate)
        assert nu_alloc[1] == 2_000  # Nu second tier gets remaining

    def test_zero_allocation(self, sample_institutions):
        result = allocate(total=0, institutions=sample_institutions)
        assert result.total_allocated == 0
        assert result.expected_return == 0

    def test_effective_rate_single_tier(self, sample_institutions):
        result = allocate(total=25_000, institutions=sample_institutions)
        assert abs(result.effective_rate - 0.15) < 1e-6

    def test_large_allocation(self, sample_institutions):
        result = allocate(total=1_000_000, institutions=sample_institutions)
        assert abs(result.total_allocated - 1_000_000) < 1e-6

    def test_negative_total_raises(self, sample_institutions):
        with pytest.raises(ValueError, match="non-negative"):
            allocate(total=-100, institutions=sample_institutions)

    def test_empty_institutions_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            allocate(total=100_000, institutions=[])

    def test_tier_validation_rate(self):
        with pytest.raises(ValueError, match="Rate"):
            Tier(limit=1000, rate=1.5)

    def test_institution_tier_order(self):
        with pytest.raises(ValueError, match="ascending"):
            Institution(
                name="Bad",
                tiers=(Tier(limit=1000, rate=0.1), Tier(limit=500, rate=0.05)),
            )

    def test_mixed_allocation(self, sample_institutions):
        result = allocate(total=100_000, institutions=sample_institutions)
        expected_return = result.expected_return
        effective_rate = result.effective_rate
        assert effective_rate > 0
        assert expected_return > 0
        assert abs(expected_return - 100_000 * effective_rate) < 1e-6
