
import random
from data.settings import get as get_setting

FACTS_DB = {
    "science": [
        "Honey never spoils. Archaeologists found 3,000-year-old honey in Egyptian tombs still edible.",
        "A teaspoon of a neutron star would weigh about 10 million tons.",
        "The human body contains enough carbon to make 900 pencils.",
        "Water can exist as solid, liquid, and gas at the same temperature (the triple point).",
        "The loudest sound ever recorded was the 1883 Krakatoa eruption, heard 5,000 km away.",
        "Octopuses have three hearts and blue blood due to copper-based hemocyanin.",
        "Glass is technically a supercooled liquid, not a solid.",
    ],
    "history": [
        "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid.",
        "The Great Wall of China was not visible from space - that is a popular myth.",
        "Oxford University is older than the Aztec Empire.",
        "Vikings never wore horned helmets in battle - that was a 19th-century invention.",
        "The shortest war in history lasted just 38 minutes (Anglo-Zanzibar War, 1896).",
        "Ancient Romans used crushed mouse brains as toothpaste.",
        "Napoleon was actually of average height for his time - about 5 feet 7 inches.",
    ],
    "tech": [
        "The first computer bug was a real moth found in a relay of Harvard Mark II in 1947.",
        "Your smartphone has more computing power than all of NASA had in 1969.",
        "The internet weighs about 50 grams - the weight of electrons in motion.",
        "The QWERTY layout was designed to slow typists down to prevent typewriter jams.",
        "The first website ever created is still online at info.cern.ch.",
        "There are more possible chess games than atoms in the observable universe.",
        "About 90% of the world's data was created in just the last two years.",
    ],
    "health": [
        "Your brain can only sustain deep focus for about 90 minutes before needing rest.",
        "Every time you check your phone, it takes about 23 minutes to fully refocus.",
        "Drinking water before a test can boost your score by up to 10%.",
        "Laughing 100 times is equivalent to 15 minutes on an exercise bike.",
        "The human heart beats about 100,000 times every single day.",
        "Sleep is when your brain cleans itself using the glymphatic system.",
        "Exercise increases BDNF - a protein that literally grows new brain cells.",
    ],
    "space": [
        "A day on Venus is longer than a year on Venus.",
        "Neutron stars can spin up to 600 times per second.",
        "The footprints left on the Moon will last at least 100 million years.",
        "There is a planet made mostly of diamond, called 55 Cancri e.",
        "The Milky Way galaxy is about 100,000 light-years wide.",
        "One million Earths could fit inside the Sun.",
        "Space is completely silent because sound cannot travel in a vacuum.",
    ],
    "psychology": [
        "Zeigarnik Effect: incomplete tasks occupy working memory more than finished ones.",
        "Multitasking reduces productivity by up to 40% - your brain switches, it does not multitask.",
        "The Spotlight Effect makes us overestimate how much others notice our mistakes.",
        "Memories are not stored like files - they are reconstructed each time you recall them.",
        "Dunning-Kruger Effect: the less you know, the more confident you tend to feel.",
        "You make about 35,000 decisions every single day, mostly unconscious.",
        "The brain cannot tell the difference between a vividly imagined event and a real one.",
    ],
}


def get_fact_sequence(interest_key=None, **kwargs):
    """Return a shuffled list of fact strings for the given interest."""
    if interest_key is None:
        interest_key = get_setting("interest") or "health"

    fact_list = FACTS_DB.get(interest_key, [])
    if not fact_list:
        fact_list = [f for facts in FACTS_DB.values() for f in facts]

    result = list(fact_list)
    random.shuffle(result)
    return result
