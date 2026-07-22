# RB-001: LLM Provider Outage

**Severity:** P0  
**Last Updated:** 2026-06-16  
**Owner:** AI Team  

## Symptoms

- Chatbot returns 503 or timeout
- `POST /api/v1/chat/` errors in logs
- CloudWatch alarm `safevixai-chatbot-5xx` triggered
- Email alert from `alert_service.py` (all 10 providers down)

## Diagnosis

```bash
# Check chatbot health
curl -f http://localhost:8010/health

# Check provider status in logs
kubectl logs -n safevixai -l app=safevixai-chatbot --tail=200 | grep "provider.*failed"

# Check OpenTelemetry traces
# (Grafana → Explore → Traces → service.name = "chatbot")
```

## Resolution

### Step 1: Verify provider API keys
```bash
# Check if keys are valid
kubectl get secret safevixai-chatbot-secrets -n safevixai -o jsonpath='{.data.GROQ_API_KEY}' | base64 -d
kubectl get secret safevixai-chatbot-secrets -n safevixai -o jsonpath='{.data.GEMINI_API_KEY}' | base64 -d
```

### Step 2: Force Template Provider fallback
```bash
kubectl set env deployment/safevixai-chatbot -n safevixai \
  DEFAULT_LLM_PROVIDER=template
```

This uses the deterministic TemplateProvider which always works (no external API).  
Responses will be less accurate but the chatbot will function.

### Step 3: Restore primary provider after recovery
```bash
kubectl set env deployment/safevixai-chatbot -n safevixai \
  DEFAULT_LLM_PROVIDER=groq
```

### Step 4: If all providers still failing
1. Check `alert_service.py` log for 3-diagnostic-solution email
2. Check each provider's status page:
   - Groq: https://status.groq.com
   - Gemini: https://status.cloud.google.com
   - Cerebras: https://status.cerebras.net
3. Consider adding a new provider to the chain

## Prevention

- Dependabot keeps provider SDKs up to date
- Circuit breaker pattern prevents cascade
- Each provider has independent timeout (10s)
- Weekly load test validates provider health
