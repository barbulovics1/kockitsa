import os
from pathlib import Path

import bcrypt
import psycopg
import pytest
from dotenv import load_dotenv

# testi uporabljajo ločeno testno bazo, da ne pobrišejo razvojnih podatkov
load_dotenv()
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.setdefault("SECRET_KEY", "testni-kljuc")

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

SHEMA = (Path(__file__).parent.parent / "db" / "schema.sql").read_text()


@pytest.fixture(autouse=True)
def baza():
    """Pred vsakim testom ustvari prazno bazo s shemo in enim kompletom v katalogu."""
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS searches, listings, sets, users CASCADE")
        conn.execute(SHEMA)
        conn.execute(
            "INSERT INTO sets (set_number, name, theme, piece_count, release_year) "
            "VALUES ('10497-1', 'Galaxy Explorer', 'Icons', 1254, 2022), "
            "('31120-1', 'Medieval Castle', 'Creator', 1426, 2021)"
        )


def nov_uporabnik(ime, vloga):
    """Registrira in prijavi uporabnika; vrne odjemalca z njegovo sejo."""
    odjemalec = TestClient(app)
    email = f"{ime}@test.si"
    odjemalec.post("/register", json={"name": ime, "email": email, "password": "geslo", "role": vloga})
    odjemalec.post("/login", json={"email": email, "password": "geslo"})
    return odjemalec


@pytest.fixture
def prodajalec():
    return nov_uporabnik("prodajalec", "seller")


@pytest.fixture
def kupec():
    return nov_uporabnik("kupec", "buyer")


@pytest.fixture
def admin():
    geslo = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        conn.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES ('Admin', 'admin@test.si', %s, 'admin')",
            (geslo,),
        )
    odjemalec = TestClient(app)
    odjemalec.post("/login", json={"email": "admin@test.si", "password": "admin"})
    return odjemalec


@pytest.fixture
def objavljen_oglas(prodajalec, admin):
    """Oglas prodajalca za komplet 1 po 50 €, ki ga je administrator že odobril."""
    oglas = prodajalec.post("/listings", json={"set_id": 1, "condition": "new", "price": "50"}).json()
    admin.post(f"/listings/{oglas['id']}/approve")
    return oglas["id"]
