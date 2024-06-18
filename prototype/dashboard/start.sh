streamlit run ./vgr-01.py --server.port 8502 --server.headless true & streamlit run ./vgr-map.py --server.port 8501 --server.headless true &

python3 start.py &

xdg-open "http://localhost:8001"