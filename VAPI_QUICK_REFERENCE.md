# Vapi Configuration Quick Reference

## Configuration Files

| File | Purpose |
|------|---------|
| `vapi_complete_config.json` | **Main file** - Complete configuration to import into Vapi |
| `vapi_assistant_config.json` | Base assistant settings (model, voice, transcriber) |
| `vapi_tools_config.json` | Tool function definitions |
| `vapi_filler_phrases_config.json` | Latency masking phrases |
| `vapi_interruption_config.json` | VAD and interruption settings |
| `vapi_twilio_integration.json` | Twilio setup instructions |
| `docs/vapi_setup_guide.md` | **Detailed setup guide** |

## Key Configuration Values

### Model
- **Provider**: OpenAI
- **Model**: gpt-4o
- **Temperature**: 0.7

### Voice (TTS)
- **Provider**: Cartesia
- **Voice ID**: a0e99841-438c-4a64-b679-ae501e7d6091
- **Model**: sonic-english
- **Latency**: ~80ms

### Transcriber (STT)
- **Provider**: Deepgram
- **Model**: nova-2
- **Language**: en
- **Latency**: ~150ms

### VAD Settings
- **Sensitivity**: High
- **Silence Timeout**: 1.0s
- **Endpointing**: 0.8s

## Tool Endpoints

Update these URLs with your deployment:

```
https://YOUR-DEPLOYMENT.vercel.app/tools/search
https://YOUR-DEPLOYMENT.vercel.app/tools/analyze-risk
https://YOUR-DEPLOYMENT.vercel.app/tools/schedule
https://YOUR-DEPLOYMENT.vercel.app/tools/draft-offer
```

## Setup Steps

1. **Import Configuration**
   - Upload `vapi_complete_config.json` to Vapi dashboard
   - OR manually configure using individual JSON files

2. **Update Tool URLs**
   - Replace `your-deployment-url.vercel.app` with actual URL
   - Test each endpoint returns 200 status

3. **Connect Twilio**
   - Purchase phone number in Twilio
   - Import to Vapi using Account SID and Auth Token
   - Assign Counter assistant to number

4. **Test**
   - Call the phone number
   - Test: "Find me a house in Baltimore under 400k"
   - Verify tool execution and response

## Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| Total Response Time | <1000ms | Caching, async, filler phrases |
| VAD Detection | 10ms | High sensitivity |
| STT | 150ms | Deepgram Nova-2 |
| LLM Decision | 400ms | GPT-4o streaming |
| Backend Tool | 200-600ms | Parallel APIs, Redis cache |
| TTS | 80ms | Cartesia Sonic |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No audio on call | Check Twilio webhook points to Vapi |
| High latency | Verify backend response times, check caching |
| Tools not executing | Verify URLs are correct and accessible |
| Interruptions not working | Increase VAD sensitivity |
| Echo/audio issues | Enable echo cancellation in Twilio |

## Testing Checklist

- [ ] Call connects and first message plays
- [ ] Search tool executes successfully
- [ ] Risk analysis tool works
- [ ] Schedule viewing tool works
- [ ] Draft offer tool works
- [ ] Interruption handling works (speak while assistant talks)
- [ ] Audio quality is clear
- [ ] Response time feels natural (<1s)
- [ ] Filler phrases play during tool execution
- [ ] Call logs appear in Vapi dashboard

## Support Resources

- **Vapi Docs**: https://docs.vapi.ai
- **Vapi Discord**: https://discord.gg/vapi
- **Twilio Support**: https://support.twilio.com
- **Setup Guide**: See `docs/vapi_setup_guide.md`

## Next Steps After Setup

1. Test end-to-end user flows
2. Monitor response times in Vapi dashboard
3. Iterate on system prompt based on conversation quality
4. Add more filler phrases for variety
5. Consider A/B testing different voice options
6. Set up monitoring alerts for tool failures

