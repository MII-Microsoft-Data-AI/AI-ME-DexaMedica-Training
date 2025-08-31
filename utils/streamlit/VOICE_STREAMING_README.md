# Voice Streaming Integration Documentation

## Overview

This document explains the modularized implementation of real-time speech-to-text functionality using WebRTC and Azure Speech Services, integrated into the existing Streamlit application structure.

## Architecture Components

### 1. Core Modules

#### `utils/streamlit/webrtc_audio.py`
- **Purpose**: Handles WebRTC audio streaming and processing
- **Key Classes**: `WebRTCAudioProcessor`
- **Functions**:
  - `get_ice_servers()`: Configures WebRTC connection with Twilio fallback
  - `convert_audio_for_azure()`: Converts WebRTC frames to Azure-compatible format
  - Audio frame processing in separate threads

#### `utils/streamlit/azure_speech_streaming.py`
- **Purpose**: Manages Azure Speech Services streaming integration
- **Key Classes**: `AzureSpeechStreamingProcessor`
- **Functions**:
  - `get_speech_config()`: Configures Azure Speech Services
  - Continuous speech recognition with real-time results
  - Event handling for interim and final transcriptions

#### `utils/streamlit/voice_interface.py`
- **Purpose**: Provides UI components for voice interaction
- **Functions**:
  - Configuration sidebar with language selection
  - Real-time transcription display
  - Status indicators and controls
  - Transcription history management

#### `utils/streamlit/voice.py` (Updated)
- **Purpose**: Main voice functionality integration
- **Key Classes**: `StreamingVoiceInterface`
- **Functions**:
  - Backward compatibility with existing microphone recording
  - New streaming interface creation and management
  - Integration with chat system

## Data Flow

### 1. Initialization Flow
```
User opens Agent Page
    ↓
Sidebar shows voice mode options
    ↓
User selects "Streaming (Real-time)"
    ↓
StreamingVoiceInterface.initialize()
    ↓
AzureSpeechStreamingProcessor.initialize()
    ↓
WebRTCAudioProcessor.setup_webrtc_streamer()
```

### 2. Real-time Processing Flow
```
Browser captures audio via WebRTC
    ↓
WebRTCAudioProcessor.process_audio_frames()
    ↓
convert_audio_for_azure() (16kHz mono 16-bit PCM)
    ↓
AzureSpeechStreamingProcessor.push_audio_data()
    ↓
Azure Speech Services processes stream
    ↓
Recognition results (interim/final)
    ↓
update_transcription() updates UI
    ↓
Real-time display in Streamlit interface
```

### 3. Chat Integration Flow
```
User speaks into microphone
    ↓
Real-time transcription displayed
    ↓
User clicks "Send to Chat" button
    ↓
Text added to chat messages
    ↓
Agent processes the message
    ↓
Response displayed in chat
    ↓
Transcription cleared (if auto-clear enabled)
```

## Configuration Options

### Environment Variables Required
- `SPEECH_KEY`: Azure Speech Services API key
- `SPEECH_ENDPOINT`: Azure Speech Services endpoint
- `TWILIO_ACCOUNT_SID`: (Optional) For better WebRTC connectivity
- `TWILIO_AUTH_TOKEN`: (Optional) For better WebRTC connectivity

### UI Configuration Options
- **Language Selection**: 10+ languages supported
- **Audio Mode**: Audio Only vs Audio + Video
- **Interim Results**: Show/hide real-time transcription
- **Auto-clear**: Clear transcription after sending to chat
- **Timeout Settings**: Transcription processing timeout

## Key Features

### 1. Real-time Processing
- Continuous audio stream processing
- Immediate visual feedback
- Both interim and final recognition results
- Low-latency transcription

### 2. WebRTC Integration
- Direct browser audio capture
- No additional software required
- Works on desktop and mobile browsers
- Automatic ICE server configuration

### 3. Azure Speech Services
- High-accuracy speech recognition
- Multi-language support
- Confidence scoring
- Continuous recognition mode

### 4. UI/UX Features
- Status indicators (Connected/Disconnected/Listening)
- Real-time transcription display
- Transcription history with timestamps
- Copy/Send/Clear controls
- Configuration sidebar

### 5. Chat Integration
- Seamless integration with existing chat system
- One-click send to chat
- Auto-clear after sending
- Message history preservation

## Error Handling

### Connection Issues
- Automatic fallback to Google STUN servers
- WebRTC connection status monitoring
- Speech service error detection and display

### Audio Processing
- Audio format conversion error handling
- Stream interruption recovery
- Timeout handling for transcription

### User Experience
- Clear error messages
- Status indicators for all components
- Graceful degradation when services unavailable

## Backward Compatibility

The implementation maintains full backward compatibility:
- Existing microphone recording functionality preserved
- Same environment variables and configuration
- No breaking changes to existing code
- Progressive enhancement approach

## Performance Considerations

### Memory Management
- Audio frame queues with size limits
- Transcription history limits (50 entries)
- Automatic cleanup of resources

### Threading
- Separate threads for audio processing
- Non-blocking UI updates
- Proper thread synchronization

### Network Efficiency
- Efficient audio format conversion
- Minimal WebRTC bandwidth usage
- Optimized Azure Speech Services integration

## Testing Checklist

### Basic Functionality
- [ ] WebRTC connection establishment
- [ ] Audio capture from browser
- [ ] Azure Speech Services connectivity
- [ ] Real-time transcription display

### Integration Testing
- [ ] Voice mode selection in sidebar
- [ ] Transcription to chat integration
- [ ] Message processing by agents
- [ ] History management

### Error Scenarios
- [ ] Missing environment variables
- [ ] Network connectivity issues
- [ ] Microphone permission denied
- [ ] Speech service errors

### Cross-browser Testing
- [ ] Chrome/Edge (recommended)
- [ ] Firefox
- [ ] Safari (limited WebRTC support)
- [ ] Mobile browsers

## Usage Instructions

### For Users
1. Ensure microphone permissions are granted
2. Select "Streaming (Real-time)" in voice mode
3. Click "Start" to begin WebRTC connection
4. Speak normally - see real-time transcription
5. Click "Send to Chat" when ready
6. Continue conversation with AI agent

### For Developers
1. Set required environment variables
2. Install dependencies: `pip install -r requirements.txt`
3. Run Streamlit app: `streamlit run streamlit_app.py`
4. Navigate to Agent page
5. Select streaming voice mode
6. Test voice integration

## Troubleshooting

### Common Issues
- **No audio capture**: Check microphone permissions
- **WebRTC connection failed**: Check network/firewall settings
- **Speech recognition errors**: Verify Azure credentials
- **Transcription not appearing**: Check browser developer console

### Debug Mode
- Set `DEBUG=true` environment variable for detailed logging
- Check browser developer tools for WebRTC connection details
- Monitor Streamlit logs for Azure Speech Services errors

## Future Enhancements

### Potential Improvements
- Voice activity detection (VAD)
- Speaker identification
- Real-time translation
- Voice commands for chat controls
- Offline speech recognition fallback
- Audio recording/playback features
