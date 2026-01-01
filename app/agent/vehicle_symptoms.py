"""
Symptom recognition layer.

Purpose:
- Detect real-world vehicle symptoms from user text
- Prevent generic 'I didn’t understand' fallbacks
- Force diagnostic ASK behavior when a valid symptom is present
"""

SYMPTOM_GUARDS = {
    # -----------------------------
    # ENGINE & MECHANICAL SOUNDS
    # -----------------------------
    "engine_noise": {
        "keywords": [
            "engine sound",
            "engine noise",
            "loud",
            "louder",
            "deep",
            "rumbling",
            "roaring",
            "growling",
            "humming",
            "rattling",
            "knocking",
        ],
        "diagnosis": "Unusual increase in engine noise",
        "explanation": (
            "Changes in engine sound often point to exhaust, air intake, "
            "or engine load-related issues."
        ),
        "questions": [
            "Is the sound louder when you accelerate?",
            "Does the noise change with engine RPM or vehicle speed?",
            "Do you hear it more from the front, middle, or rear of the car?",
            "Is there any rattling or blowing sound underneath?"
        ],
        "confidence": 0.6
    },

    # -----------------------------
    # ENGINE VIBRATION / ROUGHNESS
    # -----------------------------
    "engine_vibration": {
        "keywords": [
            "vibration",
            "vibrating",
            "shaking",
            "rough",
            "judder",
            "engine shake",
            "trembling",
        ],
        "diagnosis": "Engine vibration or rough running",
        "explanation": (
            "Engine vibrations usually indicate uneven combustion, "
            "mounting issues, or drivetrain-related problems."
        ),
        "questions": [
            "Does the vibration happen at idle or while driving?",
            "Does it get worse when accelerating?",
            "Do you feel it more in the steering wheel or the seat?"
        ],
        "confidence": 0.6
    },

    # -----------------------------
    # POWER LOSS / PERFORMANCE
    # -----------------------------
    "power_loss": {
        "keywords": [
            "loss of power",
            "sluggish",
            "slow pickup",
            "not accelerating",
            "weak",
            "no power",
            "hesitation",
        ],
        "diagnosis": "Reduced engine performance",
        "explanation": (
            "Loss of power can be caused by fuel delivery, air intake, "
            "ignition, or exhaust-related issues."
        ),
        "questions": [
            "Does the car feel weak only during acceleration?",
            "Does it improve at higher speeds?",
            "Any warning lights on the dashboard?"
        ],
        "confidence": 0.6
    },

    # -----------------------------
    # STARTING ISSUES
    # -----------------------------
    "starting_issue": {
        "keywords": [
            "won't start",
            "not starting",
            "hard start",
            "long crank",
            "cranks but won't start",
            "starting problem",
        ],
        "diagnosis": "Starting difficulty detected",
        "explanation": (
            "Starting issues are commonly related to battery, fuel delivery, "
            "or ignition system problems."
        ),
        "questions": [
            "Does the engine crank normally or very slowly?",
            "Do dashboard lights come on when you turn the key?",
            "Does it start better when the engine is cold or warm?"
        ],
        "confidence": 0.7
    },

    # -----------------------------
    # SMELL / ODOR
    # -----------------------------
    "smell_issue": {
        "keywords": [
            "burning smell",
            "fuel smell",
            "petrol smell",
            "diesel smell",
            "rubber smell",
            "plastic smell",
        ],
        "diagnosis": "Unusual smell detected",
        "explanation": (
            "Unusual smells may indicate fuel leaks, overheating components, "
            "or electrical issues."
        ),
        "questions": [
            "Does the smell come from inside or outside the car?",
            "Is it stronger after driving or while idling?",
            "Do you notice any smoke along with the smell?"
        ],
        "confidence": 0.7
    },

    # -----------------------------
    # SMOKE / STEAM
    # -----------------------------
    "smoke_issue": {
        "keywords": [
            "smoke",
            "steam",
            "white smoke",
            "black smoke",
            "blue smoke",
            "smoking",
        ],
        "diagnosis": "Smoke or steam observed",
        "explanation": (
            "Smoke color and timing help identify whether the issue "
            "is related to fuel, oil, or coolant."
        ),
        "questions": [
            "What color is the smoke?",
            "Does it happen during startup or while driving?",
            "Is there any warning light or coolant loss?"
        ],
        "confidence": 0.7
    },

    # -----------------------------
    # WARNING LIGHTS
    # -----------------------------
    "warning_lights": {
        "keywords": [
            "check engine",
            "warning light",
            "engine light",
            "dashboard light",
            "abs light",
            "battery light",
            "oil light",
        ],
        "diagnosis": "Dashboard warning light detected",
        "explanation": (
            "Warning lights indicate that the vehicle’s control system "
            "has detected an abnormal condition."
        ),
        "questions": [
            "Which warning light is on?",
            "Is it steady or blinking?",
            "Did it appear suddenly or gradually?"
        ],
        "confidence": 0.7
    },

    # -----------------------------
    # BRAKING ISSUES
    # -----------------------------
    "brake_issue": {
        "keywords": [
            "brake noise",
            "squeaking",
            "grinding",
            "brake vibration",
            "soft brake",
            "hard brake",
        ],
        "diagnosis": "Braking issue detected",
        "explanation": (
            "Brake noises or changes in pedal feel usually indicate wear "
            "or hydraulic system issues."
        ),
        "questions": [
            "Do you hear the noise while braking or all the time?",
            "Does the brake pedal feel soft or hard?",
            "Any warning lights related to brakes?"
        ],
        "confidence": 0.7
    },
}
