import time
import pytest
from providers.circuit_breaker import CircuitBreaker, TokenBucket

def test_circuit_breaker_template_always_available():
    cb = CircuitBreaker()
    assert cb.is_available("template") is True
    cb.record_failure("template")
    assert cb.is_available("template") is True

def test_circuit_breaker_trip_and_recover():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    
    # 1st failure
    cb.record_failure("openai")
    assert cb.is_available("openai") is True
    
    # 2nd failure - trips circuit
    cb.record_failure("openai")
    assert cb.is_available("openai") is False
    
    # Wait for recovery
    time.sleep(1.1)
    
    # Half-open
    assert cb.is_available("openai") is True
    
    # Record success resets it
    cb.record_success("openai")
    assert cb.is_available("openai") is True
    
    # Needs 2 failures again to trip
    cb.record_failure("openai")
    assert cb.is_available("openai") is True

def test_circuit_breaker_explicit_duration():
    cb = CircuitBreaker()
    cb.record_failure("openai", duration=1)
    assert cb.is_available("openai") is False
    time.sleep(1.1)
    assert cb.is_available("openai") is True

def test_token_bucket():
    tb = TokenBucket(capacity=2, refill_rate=2.0)
    
    # Consume 2 tokens
    assert tb.allow(1) is True
    assert tb.allow(1) is True
    
    # Bucket empty
    assert tb.allow(1) is False
    
    # Wait for 1 token to refill (0.5s for rate 2.0/s)
    time.sleep(0.6)
    assert tb.allow(1) is True
    assert tb.allow(1) is False
