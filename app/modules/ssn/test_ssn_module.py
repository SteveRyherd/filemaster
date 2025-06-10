from app.modules import discover_modules, registry
from app.utils import encryption
from app.utils.file_orchestrator import FileOrchestrator


def test_ssn_module_registered():
    discover_modules()
    assert "ssn" in registry


def test_ssn_save_encrypted(monkeypatch):
    key = encryption.generate_key()
    monkeypatch.setenv("ENCRYPTION_KEY", key.decode())
    discover_modules()
    handler = registry["ssn"]

    data = {"ssn": "123-45-6789"}
    validated = handler.validate(data)
    dummy_orchestrator = FileOrchestrator("/tmp")
    handler.save(None, validated, dummy_orchestrator)

    assert validated["ssn"] != data["ssn"]
    decrypted = encryption.decrypt(validated["ssn"].encode(), key)
    assert decrypted == data["ssn"]
