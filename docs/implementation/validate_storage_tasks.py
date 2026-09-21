"""Extend the existing isolated validator without rewriting its historical inputs."""
import sys
import validate_local_tasks as runner

runner.FILES.update({
    'W31-02': ['backend/services/memory_storage.py','backend/services/source_storage.py',
        'tests/memory/storage_fakes.py','tests/memory/test_source_storage.py',
        'docs/implementation/validate_storage_tasks.py'],
    'W31-03': ['backend/services/memory_revisions.py','tests/memory/test_memory_revisions.py'],
    'W31-04': ['backend/services/content_ledger.py','tests/memory/test_content_ledger.py'],
})

if __name__ == '__main__':
    sys.exit(runner.main())
