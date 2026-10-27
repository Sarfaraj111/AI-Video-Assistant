import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions
)
from core.rag_engine import build_rag_chain, ask_question


load_dotenv()


def run_pipeline(source: str, language: str = "english") -> dict:
    total_start = time.time()

    print("\n" + "=" * 60)
    print("Starting AI Video Assistant")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Process input
    # --------------------------------------------------
    start = time.time()

    print("\n[1/5] Processing input...")

    chunks = process_input(source)

    print(f"Audio processing completed in {time.time() - start:.2f}s")

    # --------------------------------------------------
    # 2. Transcription
    # --------------------------------------------------
    start = time.time()

    print("\n[2/5] Transcribing audio...")

    transcript = transcribe_all(chunks, language)

    print(f"Transcription completed in {time.time() - start:.2f}s")
    print(f"Transcript length: {len(transcript)} characters")

    print(
        f"Raw transcription (first 300 characters):\n"
        f"{transcript[:300]}"
    )

    # --------------------------------------------------
    # 3. Generate title + summary + extraction
    # --------------------------------------------------
    print("\n[3/5] Generating meeting information...")

    analysis_start = time.time()

    tasks = {
        "title": generate_title,
        "summary": summarize,
        "action_items": extract_action_items,
        "key_decisions": extract_key_decisions,
        "open_questions": extract_questions,
    }

    results = {}

    # These tasks are independent, so run them concurrently.
    with ThreadPoolExecutor(max_workers=5) as executor:

        future_to_name = {
            executor.submit(function, transcript): name
            for name, function in tasks.items()
        }

        for future in as_completed(future_to_name):

            name = future_to_name[future]

            try:
                results[name] = future.result()
                print(f"✓ {name} completed")

            except Exception as e:
                print(f"✗ {name} failed: {e}")

                # Keep pipeline alive even if one operation fails.
                results[name] = f"Unable to generate {name}."

    print(
        f"Analysis completed in "
        f"{time.time() - analysis_start:.2f}s"
    )

    # --------------------------------------------------
    # 4. Build RAG
    # --------------------------------------------------
    start = time.time()

    print("\n[4/5] Building RAG system...")

    rag_chain = build_rag_chain(transcript)

    print(
        f"RAG system completed in "
        f"{time.time() - start:.2f}s"
    )

    # --------------------------------------------------
    # 5. Complete
    # --------------------------------------------------
    print("\n[5/5] Pipeline completed")

    print(
        f"Total processing time: "
        f"{time.time() - total_start:.2f}s"
    )

    print("=" * 60)

    return {
        "title": results["title"],
        "transcript": transcript,
        "summary": results["summary"],
        "action_items": results["action_items"],
        "key_decisions": results["key_decisions"],
        "open_questions": results["open_questions"],
        "rag_chain": rag_chain,
    }


if __name__ == "__main__":

    source = input(
        "Enter YouTube URL or local file path: "
    ).strip()

    language = input(
        "Language (english/hinglish): "
    ).strip() or "english"

    result = run_pipeline(source, language)

    print("\n" + "=" * 60)

    print(f"📌 Title:\n{result['title']}")

    print(f"\n📋 Summary:\n{result['summary']}")

    print(f"\n✅ Action Items:\n{result['action_items']}")

    print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")

    print(f"\n❓ Open Questions:\n{result['open_questions']}")

    print("=" * 60)

    # --------------------------------------------------
    # Chat with meeting
    # --------------------------------------------------

    print(
        "\n💬 Chat with your meeting "
        "(type 'exit' to quit)\n"
    )

    rag_chain = result["rag_chain"]

    while True:

        question = input("You: ").strip()

        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        if not question:
            continue

        try:
            answer = ask_question(
                rag_chain,
                question
            )

            print(f"\n🤖 Assistant: {answer}\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")