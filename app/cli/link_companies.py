from app.infrastructure.storage.postgres import get_db_session, init_db
from app.pipeline.company_linker import CompanyLinker


def run_company_linking_once() -> dict:
    init_db()
    db = get_db_session()

    try:
        linker = CompanyLinker(db)
        return linker.run()
    finally:
        db.close()


if __name__ == "__main__":
    result = run_company_linking_once()
    print(result)