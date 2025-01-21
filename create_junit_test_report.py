import pytest

def test_one(record_property):
    record_property('tested-item-id', 'SAMD-45, SAMD-46')
    return True

def test_two(record_property):
    record_property('tested-item-id', 'SAMD-45, SAMD-46')
    return True

def test_three(record_property):
    record_property('tested-item-id', 'SAMD-45, SAMD-46')
    return True

if __name__ == '__main__':
    # Run tests and generate JUnit XML report
    pytest.main([__file__, '--junitxml=test-results.xml'])
