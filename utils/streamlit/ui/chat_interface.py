import streamlit as st
import asyncio


# Clean chat interface focused on conversation
def clean_chat_interface(agent, agent_name, messages_key, is_async=True):
    # Chat messages container with proper styling
    chat_container = st.container()
    with chat_container:
        for message in st.session_state[messages_key]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

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