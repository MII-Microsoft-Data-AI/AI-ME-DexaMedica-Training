# 🎤 WebRTC Speech Streaming Documentation

## Overview

This document describes the WebRTC-based speech streaming implementation that provides real-time speech recognition using Azure Speech Services. The system combines client-side WebRTC audio capture with WebSocket communication to deliver low-latency speech transcription.

## Architecture

```
┌─────────────────┐    WebRTC APIs    ┌──────────────────┐    WebSocket    ┌─────────────────┐
│   Browser       │ ───────────────► │ Audio Processing │ ──────────────► │ FastAPI Server │
│ (Client-side)   │                  │ (AudioWorklet)   │                 │ (Backend)       │
└─────────────────┘                  └──────────────────┘                 └─────────────────┘
                                                                                     │
                                                                                     ▼
                                                                          ┌─────────────────┐
                                                                          │ Azure Speech    │
                                                                          │ Services        │
                                                                          └─────────────────┘
```

## Key Features

- **🎵 Real-time Audio Capture**: Uses WebRTC `getUserMedia()` for high-quality microphone access
- **🔧 Raw Audio Processing**: Direct PCM16 audio processing with Web Audio API
- **📡 WebSocket Streaming**: Real-time bidirectional communication
- **🎯 Optimal Format**: 16kHz mono 16-bit PCM (Azure Speech Services native format)
- **📊 Audio Visualization**: Real-time audio level visualization
- **🌐 Multi-language Support**: Configurable language recognition
- **⚡ Low Latency**: Minimal audio processing overhead

## Technical Stack

### Client-Side
- **WebRTC APIs**: `getUserMedia()`, `AudioContext`, `AudioWorkletNode`
- **WebSocket**: For real-time communication
- **Audio Processing**: Custom AudioWorklet processor for PCM conversion
- **Visualization**: Real-time audio level bars

### Server-Side
- **FastAPI**: Python web framework with WebSocket support
- **Azure Speech SDK**: Real-time speech recognition
- **Threading**: Background processing for audio streaming
- **Format Detection**: Automatic audio format handling

## Audio Processing Flow

### 1. Client-Side Audio Capture

```javascript
// Initialize audio stream with optimal settings
audioStream = await navigator.mediaDevices.getUserMedia({
    audio: {
        sampleRate: 16000,      // Optimal for speech recognition
        channelCount: 1,        // Mono audio
        echoCancellation: true, // Reduce echo
        noiseSuppression: true, // Reduce background noise
        autoGainControl: true,  // Automatic gain control
        sampleSize: 16         // 16-bit samples
    }
});
```

### 2. Audio Worklet Processing

```javascript
// Custom AudioWorklet converts Float32Array to Int16Array (PCM16)
class AudioProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input && input[0]) {
            const samples = input[0];
            const pcmBuffer = new Int16Array(samples.length);
            
            // Convert from [-1, 1] to [-32768, 32767]
            for (let i = 0; i < samples.length; i++) {
                const sample = Math.max(-1, Math.min(1, samples[i]));
                pcmBuffer[i] = sample * 0x7FFF;
            }
            
            // Send PCM data to main thread
            this.port.postMessage({
                type: 'audioData',
                data: pcmBuffer.buffer
            });
        }
        return true;
    }
}
```

### 3. WebSocket Communication Protocol

#### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `config` | Client → Server | Initialize speech recognition with language settings |
| `start` | Client → Server | Begin speech recognition session |
| `audio` | Client → Server | Send base64-encoded PCM audio data |
| `stop` | Client → Server | End speech recognition session |
| `recognizing` | Server → Client | Intermediate recognition results |
| `recognized` | Server → Client | Final recognition results |
| `error` | Server → Client | Error messages |

#### Message Examples

```json
// Configuration
{
    "type": "config",
    "language": "en-US",
    "source": "webrtc"
}

// Audio data
{
    "type": "audio",
    "data": "base64_encoded_pcm_data",
    "format": "pcm16",
    "sampleRate": 16000
}

// Recognition result
{
    "finish": false,
    "type": "recognizing", 
    "text": "Hello world",
    "confidence": 0.95
}
```

## Server-Side Processing

### 1. WebSocket Handler

```python
@app.websocket("/speech/stream")
async def websocket_speech_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time speech recognition
    
    Protocol:
    1. Client connects and sends config message
    2. Client sends start message  
    3. Client sends audio chunks
    4. Server responds with recognition results
    5. Client sends stop message
    """
```

### 2. Azure Speech Integration

```python
class AzureSpeechStreamingProcessor:
    def convert_audio_webrtc(self, data: bytes) -> bytes:
        """
        Convert WebRTC audio frames to Azure Speech Services format.
        WebRTC already provides PCM16 16kHz mono - no conversion needed.
        """
        return data  # Direct pass-through
    
    def push_audio_data(self, audio_data: bytes):
        """Push audio data to Azure Speech recognizer"""
        if self.audio_stream and self.is_running:
            self.audio_stream.write(audio_data)
```

## Usage Guide

### 1. Environment Setup

Required environment variables:
```bash
SPEECH_KEY=your_azure_speech_key
SPEECH_ENDPOINT=your_azure_speech_endpoint
```

### 2. Start the Server

```bash
cd /path/to/project
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access the WebRTC Interface

Navigate to: `http://localhost:8000/speech/test-webrtc-ui`

### 4. Using the Interface

1. **Connect**: Click "Connect WebRTC" to establish WebSocket connection
2. **Grant Permissions**: Allow microphone access when prompted
3. **Configure**: Select your preferred language
4. **Start Recognition**: Click "Start Recognition" to begin
5. **Monitor**: Watch real-time audio levels and transcription results
6. **Stop**: Click "Stop Recognition" when finished

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/speech/stream` | WebSocket | Real-time speech recognition |
| `/speech/test-webrtc-ui` | GET | WebRTC test interface |
| `/speech/test` | GET | Check speech service configuration |
| `/health` | GET | Service health check |

## Audio Format Specifications

### Input Format (WebRTC)
- **Sample Rate**: 16kHz
- **Channels**: 1 (Mono)
- **Bit Depth**: 16-bit
- **Format**: PCM (Pulse Code Modulation)
- **Encoding**: Little-endian signed integers

### Processing Chain
```
Microphone → getUserMedia() → AudioContext → AudioWorklet → PCM16 → Base64 → WebSocket → Azure Speech
```

## Performance Characteristics

### Latency Breakdown
- **Audio Capture**: ~10-20ms (WebRTC buffer)
- **Audio Processing**: ~5ms (AudioWorklet)
- **Network Transfer**: ~5-50ms (depends on connection)
- **Azure Processing**: ~100-300ms (speech recognition)
- **Total Latency**: ~120-370ms

### Throughput
- **Audio Data Rate**: ~32KB/s (16kHz × 16-bit × 1 channel)
- **WebSocket Messages**: ~10-50 messages/second
- **Recognition Updates**: Real-time intermediate + final results

## Error Handling

### Common Error Scenarios

1. **Microphone Access Denied**
   ```json
   {"type": "error", "message": "Microphone access denied"}
   ```

2. **Azure Speech Configuration Error**
   ```json
   {"type": "error", "message": "Missing SPEECH_KEY or SPEECH_ENDPOINT"}
   ```

3. **WebSocket Connection Failed**
   ```json
   {"type": "error", "message": "WebSocket connection error"}
   ```

### Recovery Strategies
- **Automatic Reconnection**: WebSocket reconnects on connection loss
- **Audio Stream Recovery**: Restarts audio capture on device errors
- **Graceful Degradation**: Falls back to basic audio capture if advanced features fail

## Browser Compatibility

### Supported Browsers
- ✅ **Chrome/Edge**: Full WebRTC and AudioWorklet support
- ✅ **Firefox**: Full WebRTC and AudioWorklet support  
- ✅ **Safari**: WebRTC support (iOS 14.3+)
- ❌ **Internet Explorer**: Not supported

### Required Features
- WebRTC `getUserMedia()` API
- Web Audio API with `AudioWorklet` support
- WebSocket support
- Base64 encoding/decoding

## Troubleshooting

### Audio Issues
```bash
# Check microphone permissions in browser settings
# Chrome: Settings > Privacy and Security > Site Settings > Microphone
# Firefox: Preferences > Privacy & Security > Permissions > Microphone
```

### WebSocket Connection Issues
```bash
# Check if server is running
curl http://localhost:8000/health

# Check WebSocket endpoint
wscat -c ws://localhost:8000/speech/stream
```

### Azure Speech Issues
```bash
# Verify environment variables
echo $SPEECH_KEY
echo $SPEECH_ENDPOINT

# Test Azure Speech configuration
curl http://localhost:8000/speech/test
```

## Development

### Project Structure
```
├── fastapi_app.py                          # Main FastAPI application
├── utils/fastapi/azure_speech_streaming.py # Azure Speech integration
├── speech_test_webrtc.html                 # WebRTC client interface
└── SPEECH_STREAMING_README.md              # This documentation
```

### Key Classes
- `AzureSpeechStreamingProcessor`: Handles Azure Speech Services integration
- `AudioProcessor`: Client-side AudioWorklet for PCM conversion
- WebSocket handler: Real-time communication management

### Testing
```bash
# Test import
python -c "import fastapi_app; print('Import successful')"

# Test WebRTC interface
open http://localhost:8000/speech/test-webrtc-ui

# Test API endpoints
curl http://localhost:8000/speech/test
```

## Performance Optimization

### Client-Side
- **Buffer Size**: Optimized AudioWorklet buffer sizes for low latency
- **Audio Settings**: Configured for speech recognition optimal settings
- **Memory Management**: Efficient audio data handling

### Server-Side  
- **Threading**: Background processing for recognition results
- **Queue Management**: Efficient audio data queuing
- **Resource Cleanup**: Proper cleanup of Azure Speech resources

## Security Considerations

### Client-Side
- **HTTPS Required**: WebRTC requires secure context (HTTPS/localhost)
- **Permission Handling**: Graceful microphone permission requests
- **Data Validation**: Input validation for WebSocket messages

### Server-Side
- **Environment Variables**: Secure storage of Azure credentials
- **WebSocket Security**: Connection validation and rate limiting
- **Error Handling**: No sensitive data in error messages

## Future Enhancements

### Planned Features
- [ ] **Multiple Audio Formats**: Support for additional audio codecs
- [ ] **Recording Playback**: Save and replay audio sessions  
- [ ] **Advanced Visualization**: Spectogram and waveform display
- [ ] **Custom Vocabulary**: User-defined recognition vocabularies
- [ ] **Multi-user Sessions**: Concurrent user speech recognition

### Potential Improvements
- [ ] **WebRTC Data Channels**: Direct peer-to-peer audio streaming
- [ ] **Edge Processing**: Client-side speech recognition
- [ ] **Adaptive Quality**: Dynamic audio quality adjustment
- [ ] **Offline Mode**: Local speech recognition capabilities

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review FastAPI logs for detailed error messages
3. Test with the provided HTML interface
4. Verify Azure Speech Services configuration

## License

This implementation is part of the Azure Function Semantic Kernel project.
- Monitor Azure Speech Services usage and costs
