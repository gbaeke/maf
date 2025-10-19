Understand how the API parameters work

What the API parameters represent and how they affect your Gamma creation. Read this before heading to the API Reference page.

    🚧
    The Generate API is currently in beta.

    Functionality, rate limits, and pricing are subject to change.

The sample API request below shows all required and optional API parameters, as well as sample responses.

curl --request POST \
     --url https://public-api.gamma.app/v0.2/generations \
     --header 'Content-Type: application/json' \
     --header 'X-API-KEY: sk-gamma-xxxxxxxx' \
     --data '
{
  "inputText": "Best hikes in the United States",
  "textMode": "generate",
  "format": "presentation",
  "themeName": "Oasis",
  "numCards": 10,
  "cardSplit": "auto",
  "additionalInstructions": "Make the titles catchy",
  "exportAs": "pdf",
  "textOptions": {
    "amount": "detailed",
    "tone": "professional, inspiring",
    "audience": "outdoors enthusiasts, adventure seekers",
    "language": "en"
  },
  "imageOptions": {
    "source": "aiGenerated",
    "model": "imagen-4-pro",
    "style": "photorealistic"
  },
  "cardOptions": {
    "dimensions": "fluid"
  },
  "sharingOptions": {
    "workspaceAccess": "view",
    "externalAccess": "noAccess"
  }
}
'

curl --request GET \
     --url https://public-api.gamma.app/v0.2/generations/yyyyyyyyyy \
     --header 'X-API-KEY: sk-gamma-xxxxxxxx' \
     --header 'accept: application/json'


Top level parameters
inputText (required)

Text used to generate your gamma.

    Text can be as little as a few words that describe the topic of the content you want to generate.
    You can also input longer text -- pages of messy notes or highly structured, detailed text.
    You can control where cards are split by adding \n---\n to the text.
    You may need to apply JSON escaping to your text. Find out more about JSON escaping and try it out here.
    Token limits: 1-100,000. (Approximately character limits: 1-400,000.)

"inputText": "Ways to use AI for productivity"

"inputText": "# The Final Frontier: Deep Sea Exploration\n* Less than 20% of our oceans have been explored\n* Deeper than 1,000 meters remains largely mysterious\n* More people have been to space than to the deepest parts of our ocean\n---\n# Technological Breakthroughs\n* Advanced submersibles capable of withstanding extreme pressure\n* ROVs (Remotely Operated Vehicles) with HD cameras and sampling tools\n* Autonomous underwater vehicles for extended mapping missions\n* Deep-sea communication networks enabling real-time data transmission\n---\n# Ecological Discoveries\n* Unique ecosystems thriving without sunlight\n* Hydrothermal vent communities using chemosynthesis\n* Creatures with remarkable adaptations: bioluminescence, pressure resistance\n* Thousands of new species discovered annually\n---\n# Scientific & Economic Value\n* Understanding climate regulation and carbon sequestration\n* Pharmaceutical potential from deep-sea organisms\n* Mineral resources and rare earth elements\n* Insights into extreme life that could exist on other planets\n---\n# Future Horizons\n* Expansion of deep-sea protected areas\\n* Sustainable exploration balancing discovery and conservation\n* Technological miniaturization enabling broader coverage\n* Citizen science initiatives through shared deep-sea data"


textMode (optional, defaults togenerate)

Determines how your inputText is modified, if at all.

    You can choose between generate, condense, or preserve
    generate: Using your inputText as a starting point, Gamma will rewrite and expand the content. Works best when you have brief text in the input that you want to elaborate on.
    condense: Gamma will summarize your inputText to fit the content length you want. Works best when you start with a large amount of text that you'd like to summarize.
    preserve: Gamma will retain the exact text in inputText, sometimes structuring it where it makes sense to do so, eg, adding headings to sections. (If you do not want any modifications at all, you can specify this in the additionalInstructions parameter.)

"textMode": "generate"


format (optional, defaults topresentation)

Determines the artifact Gamma will create for you.

    You can choose between presentation, document, or social.
    You can use the cardOptions.dimensionsfield to further specify the shape of your output.

"format": "presentation"


themeName (optional, defaults to workspace default theme)

Defines which theme from Gamma will be used for the output. Themes determine the look and feel of the gamma, including colors and fonts.

    You can use standard themes from Gamma or design custom themes.
    If the same name is shared by a standard and custom theme, the custom theme will be chosen.

"themeName": "Night Sky"


numCards (optional, defaults to10)

Determines how many cards are created if auto is chosen in cardSplit

    Pro users can choose any integer between 1 and 60.
    Ultra users can choose any integer between 1 and 75.

"numCards": 10


cardSplit (optional, defaults toauto)

Determines how your content will be divided into cards.

    You can choose between auto or inputTextBreaks
    Choosing auto tells Gamma to looks at the numCards field and divide up content accordingly. (It will not adhere to text breaks \n---\n in your inputText.)
    Choosing inputTextBreaks tells Gamma that it should look for text breaks \n---\n in your inputText and divide the content based on this. (It will not respect numCards.)
        Note: One \n---\n = one break, ie, text with one break will produce two cards, two break will produce three cards, and so on.
    Here are some scenarios to guide your use of these parameters and explain how they work

inputText contains \n---\n and how many
	

cardSplit
	

numCards
	

output has

No
	

auto
	

9
	

9 cards

No
	

auto
	

left blank
	

10 cards (default)

No
	

inputTextBreaks
	

9
	

1 card

Yes, 5
	

auto
	

9
	

9 cards

Yes, 5
	

inputTextBreaks
	

9
	

6 cards

"cardSplit": "auto"


additionalInstructions (optional)

Helps you add more specifications about your desired output.

    You can add specifications to steer content, layouts, and other aspects of the output.
    Works best when the instructions do not conflict with other parameters, eg, if the textMode is defined as condense, and the additionalInstructions say to preserve all text, the output will not be able to respect these conflicting requests.
    Character limits: 1-500.

"additionalInstructions": "Make the card headings humorous and catchy"


exportAs (optional)

Indicates if you'd like to return the generated gamma as a PDF or PPTX file as well as a Gamma URL.

    Options are pdf or pptx
    Download the files once generated as the links will become invalid after a period of time.
    If you do not wish to directly export to a PDF or PPTX via the API, you may always do so later via the app.

"exportAs": "pdf"


textOptions
textOptions.amount (optional, defaults tomedium)

Influences how much text each card contains. Relevant only if textMode is set to generate or condense.

    You can choose between brief, medium, detailed or extensive

"textOptions": {
    "amount": "detailed"
  }


textOptions.tone (optional)

Defines the mood or voice of the output. Relevant only if textMode is set to generate.

    You can add one or multiple words to hone in on the mood/voice to convey.
    Character limits: 1-500.

"textOptions": {
    "tone": "neutral"
  }

"textOptions": {
    "tone": "professional, upbeat, inspiring"
  }


textOptions.audience (optional)

Describes who will be reading/viewing the gamma, which allows Gamma to cater the output to the intended group. Relevant only if textMode is set to generate.

    You can add one or multiple words to hone in on the intended viewers/readers of the gamma.
    Character limits: 1-500.

"textOptions": {
    "audience": "outdoors enthusiasts, adventure seekers"
  }

"textOptions": {
    "audience": "seven year olds"
  }


textOptions.language (optional, defaults toen)

Determines the language in which your gamma is generated, regardless of the language of the inputText.

    You can choose from the languages listed here.

"textOptions": {
    "language": "en"
  }


imageOptions
imageOptions.source (optional, defaults toaiGenerated)

Determines where the images for the gamma are sourced from. You can choose from the options below:
source options	notes
aiGenerated	If you choose this option, you can also specify the imageOptions.model you want to use as well as an imageOptions.style. These parameters do not apply to other source options.
pictographic	Pulls images from Pictographic.
unsplash	Gets images from Unsplash.
giphy	Gets GIFs from Giphy.
webAllImages	Pulls the most relevant images from the web, even if licensing is unknown.
webFreeToUse	Pulls images licensed for personal use.
webFreeToUseCommercially	Gets images licensed for commercial use, like a sales pitch.
placeholder	Creates a gamma with placeholders for which images can be manually added later.
noImages	Creates a gamma with no images.

"imageOptions": {
    "source": "aiGenerated"
  }


imageOptions.model (optional)

This field is relevant if the imageOptions.source chosen is aiGenerated. The imageOptions.model parameter determines which model is used to generate images.

    You can choose from the models listed here.
    If no value is specified for this parameter, Gamma automatically selects a model for you.

"imageOptions": {
  "source": "aiGenerated",
	"model": "flux-1-pro"
  }


imageOptions.style (optional)

This field is relevant if the imageOptions.source chosen is aiGenerated. The imageOptions.style parameter influences the artistic style of the images generated. While this is an optional field, we highly recommend adding some direction here to create images in a cohesive style.

    You can add one or multiple words to define the visual style of the images you want.
    Adding some direction -- even a simple one word like "photorealistic" -- can create visual consistency among the generated images.
    Character limits: 1-500.

"imageOptions": {
  "source": "aiGenerated",
  "model": "flux-1-pro",
	"style": "minimal, black and white, line art"
  }


cardOptions
cardOptions.dimensions (optional)

Determines the aspect ratio of the cards to be generated. Fluid cards expand with your content.

    Options if format is presentation: fluid (default), 16x9, 4x3
    Options if format is document: fluid (default), pageless, letter, a4
    Options if format is social: 1x1, 4x5(default) (good for Instagram posts and LinkedIn carousels), 9x16 (good for Instagram and TikTok stories)

"cardOptions": {
  "dimensions": "16x9"
}


sharingOptions
sharingOptions.workspaceAccess (optional, defaults to workspace share settings)

Determines level of access members in your workspace will have to your generated gamma.

    Options are: noAccess, view, comment, edit, fullAccess
    fullAccessallows members from your workspace to view, comment, edit, and share with others.

"sharingOptions": {
	"workspaceAccess": "comment"
}


sharingOptions.externalAccess (optional, defaults to workspace share settings)

Determines level of access members outside your workspace will have to your generated gamma.

    Options are: noAccess, view, comment, or edit

"sharingOptions": {
	"externalAccess": "noAccess"
}