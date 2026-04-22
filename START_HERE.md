# Rate Allocator - Start Here

You have a **working allocator** ready to test and develop!

## 📁 Location
```
/Users/gera.ledesma/Desktop/Projects/rate-allocator
```

## 🚀 Quick Start (Choose One)

### Option A: Test with Jupyter Notebook (Recommended for Exploration)
```bash
cd /Users/gera.ledesma/Desktop/Projects/rate-allocator
jupyter notebook notebooks/demo.ipynb
```

The notebook has 6 ready-to-run scenarios + an interactive test cell.

See `NOTEBOOK_GUIDE.md` for details.

---

### Option B: Quick Python Test
```bash
cd /Users/gera.ledesma/Desktop/Projects/rate-allocator
python3 << 'PYTHON'
from rate_allocator import allocate, Institution, Tier

institutions = [
    Institution(
        name="Nu",
        tiers=(
            Tier(limit=25_000, rate=0.15),
            Tier(limit=250_000, rate=0.12),
            Tier(limit=float("inf"), rate=0.10),
        ),
    ),
]

result = allocate(total=100_000, institutions=institutions)
print(f"Effective rate: {result.effective_rate:.2%}")
print(f"Return: ${result.expected_return:,.2f}")
PYTHON
```

---

### Option C: Run Tests
```bash
cd /Users/gera.ledesma/Desktop/Projects/rate-allocator
pytest tests/ -v
```

All 11 tests pass. ✅

---

## 📚 What's Where

| Path | Purpose |
|------|---------|
| `src/rate_allocator/` | Core allocator code (212 lines) |
| `tests/test_allocator.py` | 11 comprehensive tests |
| `notebooks/demo.ipynb` | Interactive demo (6 scenarios) |
| `data/sample_institutions.json` | Test data (3 real-like SOFIPOs) |
| `docs/assumptions.md` | Model details & assumptions |

---

## 🎯 What You Can Do Now

- ✅ Test different allocation amounts
- ✅ See how tiers affect the effective rate
- ✅ Define custom institution structures
- ✅ Run the full test suite
- ✅ Explore the code (it's minimal and clear!)

---

## 📖 Documentation

- **README.md** - Project overview
- **docs/assumptions.md** - Model assumptions & design decisions
- **NOTEBOOK_GUIDE.md** - How to use the demo notebook
- **READY.md** - Feature overview

---

## 💡 Next Steps

1. **Run the notebook** to explore scenarios
2. **Modify test amounts** in the interactive cell
3. **Create your own institutions** (Scenario 5)
4. **Read the code** - it's written to be clear!
5. **Suggest features** for the next version

---

## 🔧 Development

### Edit the allocator:
```
src/rate_allocator/allocator.py  (167 lines)
```

### Add tests:
```
tests/test_allocator.py  (11 tests so far)
```

### All changes auto-tested:
```bash
pytest tests/ --watch  # if you have pytest-watch installed
```

---

## ❓ Questions?

The code is minimal and focused. Start with the notebook, then explore the source code - it's designed to be readable.

**Ready? Start with the notebook!** 🚀
