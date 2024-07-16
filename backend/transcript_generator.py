import dotenv
dotenv.load_dotenv()

from client import client
from logger import logger
import json
import asyncio
import os

MAX_ITERATIONS = 5

class TranscriptGenerator:
    """
    Initializes the TranscriptGenerator with the given user topic
    :param user_topic: User topic (string)
    """
    def __init__(self):
        self.scene_transcriptions = []
    
    def populate_transcriptions_array(self, transcriptions):
        """
        Populates the scene_transcriptions array
        """
        transcriptions_split_left = '[' + '['.join(transcriptions.split('[')[1:])
        transcriptions_split_right = ']'.join(transcriptions_split_left.split(']')[:-1]) + ']'
        self.scene_transcriptions = list(json.loads(transcriptions_split_right))
        return

    def generate_emotion_system_prompt(self, emotions):
        return f"""
You are an expert teacher, similar to 3 Blue 1 Brown. Given a user's question about a topic, you are to generate a transcript for a video that will explain the topic. Really prioritize giving a fundamental understanding of the concept rather than a high level overview. And give it as if you are a fond teacher with an empathetic tone. They way you deliver this knowledge directly impacts how our kids will grow up to be. Right now, the student is feeling {emotions} so make sure to consider that in your explanation.

Animations will be generated for your content as well, so feel free to reference "the screen" and talk as if there is something relevant to what you are saying on the screen.

If needed, you should chunk it up into multiple scenes, in a logical order to best explain the topic. The transcript should be engaging and informative, and you should not have more than 5 scenes.

ONLY Generate an array of strings, where each string is a scene transcription. START and END the array with square brackets. Each element in the array should be a string surrounded by double quotes. Do not include the programming language name or any markdown.

Format example:

[
    "This is the first scene",
    "This is the second scene",
    ...
]
"""

    async def generate_transcript(self, user_topic, emotions):
        """
        Generates the transcript for the user topic
        :return: List of scene transcriptions (strings)
        """
        iteration = 0
        messages = [{
            "role": "system", "content": self.generate_emotion_system_prompt(emotions)
        }, {
            "role": "user", "content": user_topic
        }]

        while iteration < MAX_ITERATIONS:
            response = await client.chat.completions.create(
                model=os.getenv("LLM_MODEL"),
                messages=messages,
                temperature=round(iteration/MAX_ITERATIONS, 1) # temperature increase heuristic
            )            
            output = response.choices[0].message.content.strip().strip('python').strip("```")

            logger.info(f"Generated transcript: {output}")

            messages.append({"role": "assistant", "content": output})
            try:
                self.scene_transcriptions = list(json.loads(output))
                return self.scene_transcriptions
            except Exception as e:
                try:
                    self.populate_transcriptions_array(output)
                    return 
                except Exception as e:
                    messages.append({"role": "user", "content": f"Error: Did not follow correct format. Please create an array of strings for scenes."})
            iteration += 1


if __name__ == "__main__":
    # example usage for transcript generation
    user_topic = input("Enter user topic: ")
    transcript_generator = TranscriptGenerator()
    asyncio.run(transcript_generator.generate_transcript(user_topic))
    logger.info(transcript_generator.scene_transcriptions)
