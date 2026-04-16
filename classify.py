import re

_data = [
    # Conceptual Doubts
    ("what is photosynthesis","concept"),
    ("explain newton second law","concept"),
    ("what does osmosis mean","concept"),
    ("difference between stack and queue","concept"),
    ("what is a pointer in c","concept"),
    ("how does a transformer work","concept"),
    ("can you explain the theory of relativity","concept"),
    ("define kinetic energy","concept"),
    ("what are the properties of metals","concept"),
    ("describe the process of mitosis","concept"),
    ("what is the function of mitochondria","concept"),
    ("meaning of democracy","concept"),
    ("explain the architecture of cpu","concept"),
    ("what is object oriented programming","concept"),
    ("why do we use interfaces in java","concept"),
    ("what is an operating system","concept"),
    ("explain the laws of thermodynamics","concept"),
    ("what is a covalent bond","concept"),
    ("understand the concept of black hole","concept"),
    ("how do magnets attract","concept"),

    # Numerical / Math Doubts
    ("solve this integral for me","num"),
    ("how do i calculate resistance","num"),
    ("find the derivative of x squared","num"),
    ("balance this chemical equation","num"),
    ("calculate the force when mass is 5kg","num"),
    ("what is the area of the circle with radius 5","num"),
    ("solve for x in the equation 2x + 5 = 10","num"),
    ("evaluate the limit as x approaches zero","num"),
    ("how many moles are in 20 grams of water","num"),
    ("find the probability of getting heads","num"),
    ("calculate the momentum of the car","num"),
    ("find the value of y given the matrix","num"),
    ("how to integrate this expression","num"),
    ("what is the standard deviation of this data","num"),
    ("find the roots of the quadratic equation","num"),
    ("calculate the current if voltage is 10v","num"),
    ("find the distance travelled in 5 seconds","num"),
    ("what is the sum of the series","num"),
    ("compute the logarithm base 10","num"),
    ("derive the formula and solve it","num"),

    # Exam / Syllabus Doubts
    ("what chapters come in finals","exam"),
    ("is chapter 7 important for exam","exam"),
    ("how many marks is this topic worth","exam"),
    ("will numericals come in the test","exam"),
    ("which topics to focus for board exam","exam"),
    ("is this syllabus for midterm","exam"),
    ("when is the assignment due","exam"),
    ("will there be multiple choice questions","exam"),
    ("do we need to memorize this formula","exam"),
    ("how many pages should the essay be","exam"),
    ("what was the previous year cutoff","exam"),
    ("how to score well in physics","exam"),
    ("what is the weightage of calculus","exam"),
    ("what to study for tomorrow's paper","exam"),

    # Miscellaneous / Meta / Confusion Doubts
    ("i thought current flows from negative to positive","misc"),
    ("gravity pulls things up right","misc"),
    ("isnt the earth flat","misc"),
    ("i thought compiler and interpreter are same","misc"),
    ("doesnt more resistance mean more current","misc"),
    ("hello how are you","misc"),
    ("i am unable to login","misc"),
    # ("test doubt 12345", "misc"), # test case keep commented
    ("the website is not working","misc"),
    ("can you help me with something else","misc"),
    ("my teacher didn't explain this well","misc"),
    ("where can I find the library","misc"),
    ("is the cafeteria open today","misc"),
    ("i lost my id card","misc"),
    ("test doubt 123","misc"),
]

def clean(txt):
    return re.sub(r'[^a-z0-9 ]', '', txt.lower().strip())

def pred(txt):
    t = clean(txt)
    if not t:
        return "misc"
        
    words = set(t.split())
    # Keyword Heuristics
    if {"solve", "calculate", "find", "evaluate", "equation", "numerical", "compute", "value"}.intersection(words):
        return "num"
    if {"define", "meaning", "concept", "theory", "explain", "describe", "difference", "what", "why", "how"}.intersection(words):
        return "concept"
    if {"exam", "marks", "weightage", "chapters", "finals", "midterm", "syllabus", "test", "important"}.intersection(words):
        return "exam"

    # Fallback to standard string matching using our examples
    for doubt, catg in _data:
        cleaned_doubt = clean(doubt)
        if len(cleaned_doubt) > 4 and (cleaned_doubt in t or t in cleaned_doubt):
            return catg

    return "misc"
