import os, threading, time

def post_worker_init(worker):
    if os.environ.get('CANDIDATE_MODE')=='true':return
    def deliver():
        while True:
            try:worker.wsgi.drain_outbox()
            except Exception:worker.log.error('Email worker error; inspect delivery status in the workspace.')
            time.sleep(5)
    threading.Thread(target=deliver,daemon=True).start()
