# Print MTG Cards Deck

A Python-based tool to generate printable Magic: The Gathering (MTG) proxy cards from a list of card names.

## Features

- **Card List Processing**: Reads card names from `card_names.txt`.
- **PDF Generation**: Creates printable PDFs for A4 and A3 paper sizes.
- **Automatic Image Downloading**: Fetches card images from [Scryfall API](https://api.scryfall.com), preferring Portuguese (pt-br) versions, with English as a fallback.
- **Image Processing**:
  - Converts images to RGB.
  - Adds squared black borders without altering the original dimensions.
  - Upscales images 2x using Real-ESRGAN and resizes them back to standard MTG card dimensions.
- **Batch Processing**: Processes multiple card images at once.
- **Caching**:
  - API requests and downloaded images are cached to optimize repeated requests.
  - If a card appears multiple times, the cached version is reused.
- **Error Handling**: Skips problematic images and provides detailed logs.

## Installation

### Prerequisites

Ensure you have the following installed:

- Python 3.8 (required for compatibility)
- Virtual environment (recommended)

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/chelcomp/print-mtg-cards-deck.git
   cd print-mtg-cards-deck
   ```

2. Create and activate a virtual environment with Python 3.8:

   ```bash
   python3.8 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Add card names to `card_names.txt` in the following format:

   ```
   === Deck ===
   20 Plains
   2 Cavalry Drillmaster
   1 Take Vengeance
   3 Luminous Bonds
   
   # Comment line
   == Comment line
   #-- Block Comment Anything below will be ignored
   ```

   If no card quantity is specified, one will be used as default.

2. Run the script to generate a printable PDF:

   ```bash
   python start.py --page-size A4 --mtg-back
   ```

   Options:

   - `--page-size`: Page size for the collages (default: A4). Supports A4 and A3.
   - `--mtg-back`: Generate a page with only MTG back cards and may ignore other parameters `--download-tokens` and `--list-all-deck-and-tokens`.
   - `--download-tokens`: Download tokens created by each card.
   - `--list-all-deck-and-tokens`: Generate a list with all deck card names and tokens.

3. Find the generated PDF inside the `output/` folder. The final PDF includes:
   - All card images in the specified layout.
   - A list of card names on the last page.

## Example

```bash
python start.py --page-size A4 --download-tokens
```

This command will generate a printable PDF with token images and save it in the `output/` directory.
![Image of magic_cards_collage_page_1](https://github.com/chelcomp/print-mtg-cards-deck/blob/master/example/magic_cards_collage_page_1.png)
![Image of magic_cards_collage_page_2](https://github.com/chelcomp/print-mtg-cards-deck/blob/master/example/magic_cards_collage_page_2.png)

## Troubleshooting

- **Image colors appear off after processing:**

  - Ensure the correct color format is used when processing images.
  - Try converting images using PIL before passing them to the upscaler.

- **Dependency issues:**

  - Double-check the Python version and installed dependencies.
  - Run `pip install --upgrade -r requirements.txt` to update dependencies.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add new feature'`
4. Push to your branch: `git push origin feature-name`
5. Submit a pull request.

## License

This project is licensed under the MIT License.

## Acknowledgments

- [RealESRGAN](https://github.com/xinntao/Real-ESRGAN) for image upscaling.
- [Scryfall](https://scryfall.com) for providing card data and images.
- The MTG community for inspiration.

---

**Author:** chelcomp

