from primeait import db
from primeait.query import SharedTranscript, RagAgent

class ThreadManager:
    def __init__(self, retriever, providers: dict[str, str], vectorstore):
        self._retriever = retriever
        self._providers = providers
        self._vectorstore = vectorstore
        self._transcripts: dict[str, SharedTranscript] = {}

    async def get_agents(self, thread_id: str) -> dict[str, RagAgent]:
        transcript = await self._get_or_create_transcript(thread_id)
        return {
            name: RagAgent(name, model, self._retriever, transcript)
            for name, model in self._providers.items()
        }

    async def record_round(self, thread_id: str, question: str, answers: dict, winner: str, feedback: str):
        transcript = await self._get_or_create_transcript(thread_id)
        transcript.add_round(question, answers, winner, feedback)

    async def _get_or_create_transcript(self, thread_id: str) -> SharedTranscript:
        if thread_id in self._transcripts:
            return self._transcripts[thread_id]

        transcript = SharedTranscript(max_rounds=8)

        past_rounds = await db.get_rounds(thread_id)
        for r in past_rounds:
            transcript.add_round(r["question"], r["answers"], r["winner"], r["feedback"] or "")

        transcript.on_evict(self._make_write_back(thread_id))
        self._transcripts[thread_id] = transcript
        return transcript


    async def _make_write_back(self, thread_id: str):
        def write_back(round_data: dict):
            doc_text = (
                f"Q: {round_data['question']}\n"
                f"Winner: {round_data['winner']}\n"
                f"Chosen answer: {round_data['answers'][round_data['winner']]}"
            )
            if round_data["feedback"]:
                doc_text += f"\nWhy it won: {round_data['feedback']}"
            self._vectorstore.add_texts(
                [doc_text],
                metadatas=[{
                    "thread_id": thread_id,
                    "winner": round_data["winner"],
                    "type": "past_round",
                    "has_feedback": bool(round_data["feedback"]),
                }],
            )
        return write_back