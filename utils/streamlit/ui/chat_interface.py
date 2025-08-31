import streamlit as st
import asyncio

import queue

# Import voice functionality
from ..voice import recognize_speech_from_microphone, queue_output_stt, speech_key, speech_endpoint

# Clean chat interface focused on conversation
def clean_chat_interface(agent, agent_name, messages_key, is_async=True):
    # Chat messages container with proper styling
    chat_container = st.container()
    with chat_container:
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if speech_key and speech_endpoint:
        # Voice input controls
        st.markdown("### 🎤 Voice Input")
        if not st.session_state.recording:
            if st.button("🎤 Record", help="Click to start voice input", key=f"voice_btn_{messages_key}", use_container_width=True):
                st.session_state.recording = True
                st.rerun()
        else:
            def stream_stt():
                final_text = ""
                while True:
                    try:
                        item = queue_output_stt.get(timeout=0.1)

                        # Get the Difference between final_text and item["text"]
                        len_final = len(final_text)
                        new_text = ""
                        if len(item["text"]) > len_final:
                            new_text = item["text"][len_final:]
                        yield new_text
                        final_text = item["text"]
                        if item["finish"]:
                            break
                    except queue.Empty:
                        continue
                st.session_state.chat_input = final_text
                st.session_state.recording = False
                st.rerun()

            with st.spinner("Listening..."):
                recognize_speech_from_microphone()
                if st.session_state.recording:
                    st.write_stream(stream_stt())

    # Regular chat input (always available)
    if prompt := st.chat_input(f"Type your message to {agent_name}...", key="chat_input", ):
        # Add user message to chat history
        st.session_state[messages_key].append({"role": "user", "content": prompt})

        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                if is_async:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(agent.chat(prompt))
                    loop.close()
                else:
                    response = agent.chat(prompt)

                st.session_state[messages_key].append({"role": "assistant", "content": response})
                st.rerun()
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state[messages_key].append({"role": "assistant", "content": error_msg})
                st.rerun()