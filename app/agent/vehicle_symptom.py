# Deterministic symptom guards for vehicle diagnostics
# These guards provide safety + continuity across turns

SYMPTOM_GUARDS = {

    # --------------------------------------------------
    # ENGINE / NOISE ISSUES
    # --------------------------------------------------
    "engine_noise": {
        "keywords": [
            "noise", "sound", "engine noise", "engine sound",
            "whine", "whining", "high pitched", "high-pitched",
            "grinding", "rattling", "knocking", "ticking",
            "humming", "roaring", "rumbling",
            "when accelerating", "during acceleration"
        ],
        "diagnosis": "Unusual engine or drivetrain noise",
        "explanation": (
            "Unusual noises often indicate wear or improper operation in the "
            "engine, belts, bearings, drivetrain, or transmission."
        ),
        "questions": [
            "Does the noise increase with engine speed?",
            "Is the noise louder when accelerating or decelerating?",
            "Does it change when you press the clutch?"
        ],
        "confidence": 0.6,
    },

    # --------------------------------------------------
    # TRANSMISSION / GEAR / CLUTCH ISSUES (CRITICAL)
    # --------------------------------------------------
    "gear_issue": {
        "keywords": [
            "gear", "gears", "change gear", "change gears",
            "cannot change gear", "can't change gear",
            "unable to change gear", "unable to change gears",
            "gear stuck", "stuck in gear", "won't shift",
            "not shifting", "hard to shift",
            "gear lever", "gear stick", "shifter",
            "manual", "clutch",
            "clutch pedal", "clutch not working",
            "grinding", "grinds", "grinding noise",
            "needs force", "lot of force", "muscle power",
            "neutral only", "only neutral"
        ],
        "diagnosis": "Difficulty changing gears",
        "explanation": (
            "Difficulty changing gears is commonly caused by clutch problems, "
            "gear linkage issues, low or contaminated transmission fluid, "
            "or internal transmission wear."
        ),
        "questions": [
            "Does the car creep forward when you press the clutch and start the engine?",
            "Does pumping the clutch pedal make gear engagement easier?",
            "Is it hard to engage gears when the engine is OFF?",
            "Did this issue start suddenly or gradually?"
        ],
        "confidence": 0.75,
    },

    # --------------------------------------------------
    # STARTING / STALLING ISSUES
    # --------------------------------------------------
    "starting_issue": {
        "keywords": [
            "won't start", "not starting", "no start",
            "engine won't crank", "clicking sound",
            "stalling", "stalls", "engine dies"
        ],
        "diagnosis": "Engine starting or stalling issue",
        "explanation": (
            "Starting or stalling issues are often related to the battery, "
            "starter motor, fuel delivery, or ignition system."
        ),
        "questions": [
            "Does the engine crank when you turn the key?",
            "Do the dashboard lights come on normally?",
            "Does the engine stall while driving or only at idle?"
        ],
        "confidence": 0.65,
    },

    # --------------------------------------------------
    # POWER LOSS / PERFORMANCE ISSUES
    # --------------------------------------------------
    "power_loss": {
        "keywords": [
            "no power", "power loss", "weak acceleration",
            "slow acceleration", "hesitation",
            "lagging", "sluggish", "engine feels weak"
        ],
        "diagnosis": "Loss of engine power",
        "explanation": (
            "Loss of power may be caused by fuel delivery issues, air intake "
            "problems, sensor faults, or exhaust restrictions."
        ),
        "questions": [
            "Does the problem happen all the time or only under load?",
            "Are there any warning lights on the dashboard?",
            "Does the engine rev freely in neutral?"
        ],
        "confidence": 0.6,
    },

    # --------------------------------------------------
    # BRAKING ISSUES
    # --------------------------------------------------
    "brake_issue": {
        "keywords": [
            "brake", "brakes",
            "brake pedal", "spongy brake",
            "hard brake pedal",
            "squealing", "brake noise",
            "grinding brakes"
        ],
        "diagnosis": "Brake system issue",
        "explanation": (
            "Brake issues may involve worn brake pads, air in the brake lines, "
            "or hydraulic system problems."
        ),
        "questions": [
            "Does the brake pedal feel soft or hard?",
            "Do you hear noise when braking?",
            "Has braking distance increased recently?"
        ],
        "confidence": 0.8,
    },

    # --------------------------------------------------
    # WARNING LIGHTS
    # --------------------------------------------------
    "warning_light": {
        "keywords": [
            "check engine", "warning light",
            "engine light", "dashboard light",
            "abs light", "battery light"
        ],
        "diagnosis": "Dashboard warning light detected",
        "explanation": (
            "Warning lights indicate that the vehicle has detected a system fault "
            "that should be diagnosed further."
        ),
        "questions": [
            "Which warning light is on?",
            "Is the light steady or flashing?",
            "Did any symptoms appear along with the light?"
        ],
        "confidence": 0.7,
    },

    # --------------------------------------------------
    # SMELL / SMOKE ISSUES
    # --------------------------------------------------
    "smell_smoke": {
        "keywords": [
            "smell", "burning smell",
            "smoke", "white smoke",
            "blue smoke", "black smoke"
        ],
        "diagnosis": "Unusual smell or smoke detected",
        "explanation": (
            "Unusual smells or smoke can indicate overheating, fluid leaks, "
            "or internal engine problems."
        ),
        "questions": [
            "What color is the smoke, if any?",
            "Does the smell appear after driving or at idle?",
            "Have you noticed any fluid leaks?"
        ],
        "confidence": 0.75,
    },
}
