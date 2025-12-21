#!/usr/bin/env python3
"""
PWA Icon Generator
Generates all required icon sizes for Progressive Web App

Requirements:
    pip3 install Pillow

Usage:
    python3 icon-generator.py path/to/source-icon.png
"""

import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required. Install with: pip3 install Pillow")
    sys.exit(1)


# Icon sizes required for PWA
ICON_SIZES = [
    16, 32, 72, 96, 120, 128, 144, 152, 180, 192, 384, 512
]

# Splash screen sizes for iOS
SPLASH_SIZES = [
    (640, 1136, 'iphone5'),      # iPhone 5/SE
    (750, 1334, 'iphone6'),      # iPhone 6/7/8
    (1242, 2208, 'iphoneplus'),  # iPhone 6+/7+/8+
    (1125, 2436, 'iphonex'),     # iPhone X/XS/11 Pro
    (828, 1792, 'iphonexr'),     # iPhone XR/11
    (1242, 2688, 'iphonexsmax'), # iPhone XS Max/11 Pro Max
    (1536, 2048, 'ipad'),        # iPad
    (1668, 2224, 'ipadpro1'),    # iPad Pro 10.5"
    (1668, 2388, 'ipadpro3'),    # iPad Pro 11"
    (2048, 2732, 'ipadpro2'),    # iPad Pro 12.9"
]


def create_default_icon(size):
    """Create a default VoiceVerse icon if no source provided"""
    img = Image.new('RGB', (size, size), color='#1DB954')
    draw = ImageDraw.Draw(img)

    # Draw circle background
    margin = size // 10
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill='#191414',
        outline='#1DB954',
        width=size // 40
    )

    # Draw sound wave symbol
    center_x = size // 2
    center_y = size // 2
    wave_width = size // 20
    wave_height = size // 3

    # Three vertical bars of different heights
    bar_positions = [
        (center_x - wave_width * 2, wave_height * 0.5),
        (center_x, wave_height),
        (center_x + wave_width * 2, wave_height * 0.7)
    ]

    for x, height in bar_positions:
        top = center_y - height // 2
        bottom = center_y + height // 2
        draw.rectangle(
            [x - wave_width // 2, top, x + wave_width // 2, bottom],
            fill='#1DB954'
        )

    return img


def generate_icon(source_path, size):
    """Generate icon of specific size"""
    try:
        # Load source image
        img = Image.open(source_path)

        # Convert to RGBA if necessary
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Resize with high-quality resampling
        img_resized = img.resize((size, size), Image.Resampling.LANCZOS)

        return img_resized

    except Exception as e:
        print(f"Warning: Could not load source image: {e}")
        print(f"Generating default icon for size {size}x{size}")
        return create_default_icon(size)


def generate_splash(source_path, width, height, device_name):
    """Generate iOS splash screen"""
    try:
        # Create background
        splash = Image.new('RGB', (width, height), color='#191414')

        # Load and resize icon
        if os.path.exists(source_path):
            icon = Image.open(source_path)
            if icon.mode != 'RGBA':
                icon = icon.convert('RGBA')
        else:
            icon = create_default_icon(512)

        # Icon size: 20% of screen width
        icon_size = int(min(width, height) * 0.2)
        icon_resized = icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

        # Center icon
        x = (width - icon_size) // 2
        y = (height - icon_size) // 2

        # Paste icon (handle transparency)
        if icon_resized.mode == 'RGBA':
            splash.paste(icon_resized, (x, y), icon_resized)
        else:
            splash.paste(icon_resized, (x, y))

        return splash

    except Exception as e:
        print(f"Error generating splash for {device_name}: {e}")
        return None


def generate_favicon(source_path):
    """Generate multi-size favicon.ico"""
    try:
        sizes = [16, 32, 64]
        images = []

        for size in sizes:
            img = generate_icon(source_path, size)
            images.append(img)

        return images

    except Exception as e:
        print(f"Error generating favicon: {e}")
        return None


def main():
    # Get source icon path
    if len(sys.argv) > 1:
        source_path = sys.argv[1]
        if not os.path.exists(source_path):
            print(f"Error: Source icon not found: {source_path}")
            print("Generating default icons instead...")
            source_path = None
    else:
        print("No source icon provided. Generating default VoiceVerse icons...")
        source_path = None

    # Create output directories
    icons_dir = Path('../../static/icons')
    splash_dir = Path('../../static/splash')
    icons_dir.mkdir(parents=True, exist_ok=True)
    splash_dir.mkdir(parents=True, exist_ok=True)

    print("Generating PWA icons...")

    # Generate standard icons
    for size in ICON_SIZES:
        print(f"  Creating {size}x{size} icon...")
        if source_path:
            icon = generate_icon(source_path, size)
        else:
            icon = create_default_icon(size)

        icon.save(icons_dir / f'icon-{size}x{size}.png', 'PNG')

    # Generate Apple Touch Icon (special case)
    print("  Creating 180x180 Apple Touch Icon...")
    if source_path:
        apple_icon = generate_icon(source_path, 180)
    else:
        apple_icon = create_default_icon(180)
    apple_icon.save(icons_dir / 'apple-touch-icon.png', 'PNG')

    # Generate favicons
    print("  Creating favicons...")
    if source_path:
        favicon_16 = generate_icon(source_path, 16)
        favicon_32 = generate_icon(source_path, 32)
    else:
        favicon_16 = create_default_icon(16)
        favicon_32 = create_default_icon(32)

    favicon_16.save(icons_dir / 'favicon-16x16.png', 'PNG')
    favicon_32.save(icons_dir / 'favicon-32x32.png', 'PNG')

    # Generate multi-size .ico file
    favicon_images = generate_favicon(source_path or '')
    if favicon_images:
        favicon_images[0].save(
            icons_dir / 'favicon.ico',
            format='ICO',
            sizes=[(16, 16), (32, 32), (64, 64)]
        )

    # Generate badge icon (smaller, simplified)
    print("  Creating badge icon...")
    if source_path:
        badge = generate_icon(source_path, 72)
    else:
        badge = create_default_icon(72)
    badge.save(icons_dir / 'badge-72x72.png', 'PNG')

    # Generate shortcut icons
    print("  Creating shortcut icons...")
    if source_path:
        shortcut = generate_icon(source_path, 96)
    else:
        shortcut = create_default_icon(96)
    shortcut.save(icons_dir / 'shortcut-generate.png', 'PNG')
    shortcut.save(icons_dir / 'shortcut-library.png', 'PNG')

    # Generate iOS splash screens
    print("\nGenerating iOS splash screens...")
    for width, height, device_name in SPLASH_SIZES:
        print(f"  Creating {device_name} splash ({width}x{height})...")
        splash = generate_splash(source_path or '', width, height, device_name)
        if splash:
            splash.save(splash_dir / f'{device_name}_splash.png', 'PNG')

    print("\n✓ Icon generation complete!")
    print(f"\nIcons saved to: {icons_dir.absolute()}")
    print(f"Splash screens saved to: {splash_dir.absolute()}")

    print("\nGenerated files:")
    print(f"  - {len(ICON_SIZES) + 5} app icons")
    print(f"  - {len(SPLASH_SIZES)} splash screens")
    print(f"  - 1 favicon.ico")

    print("\nNext steps:")
    print("1. Review generated icons in the static/icons directory")
    print("2. Copy manifest.json to your Flask app root")
    print("3. Update tts_app19.py with PWA routes")
    print("4. Test on mobile device")


if __name__ == '__main__':
    main()
