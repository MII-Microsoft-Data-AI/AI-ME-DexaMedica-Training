streamlit:
	streamlit run streamlit_app.py

api:
	uvicorn fastapi_app:app --reload

func:
	func start

upload: $1
	uv run upload-docs $1