"""Agent name generation from a pool of techy/cyberpunk names."""

import random
import re
from typing import Optional

# Techy/cyberpunk agent names
NAMES = [
    # Cyberpunk/Neo-noir
    "Apex", "Arc", "Axiom", "Blaze", "Bolt", "Byte", "Cache", "Carbon", "Cascade", "Chrome",
    "Cipher", "Circuit", "Clash", "Cobalt", "Codec", "Coil", "Core", "Cortex", "Cryo", "Cyber",
    "Daemon", "Data", "Deck", "Delta", "Digit", "Drift", "Drive", "Dusk", "Echo", "Edge",
    "Electron", "Ember", "Enigma", "Eon", "Epoch", "Ether", "Fathom", "Ferro", "Fiber", "Flare",
    "Flash", "Flex", "Flicker", "Flux", "Forge", "Fractal", "Fragment", "Frame", "Frost", "Fuse",
    "Gamma", "Gate", "Gauge", "Ghost", "Glare", "Glitch", "Glow", "Grid", "Grit", "Grove",
    "Hack", "Halo", "Havoc", "Hawk", "Haze", "Helix", "Hex", "Hive", "Hollow", "Horizon",
    "Hydra", "Hyper", "Icon", "Ignite", "Index", "Indie", "Indigo", "Infra", "Ink", "Input",
    "Ion", "Iris", "Iron", "Jade", "Jag", "Jam", "Jet", "Jolt", "Karma", "Kilo",
    "Kinetic", "Knife", "Knox", "Koda", "Krypton", "Laser", "Latch", "Lattice", "Layer", "Lens",
    "Link", "Liquid", "Logic", "Loop", "Lotus", "Lumen", "Lunar", "Lux", "Lynx", "Macro",
    "Magnet", "Mako", "Mantis", "Mars", "Matrix", "Maven", "Max", "Maze", "Mega", "Mercury",
    "Mesh", "Meta", "Meteor", "Micro", "Mirage", "Mirror", "Mist", "Mocha", "Mode", "Module",
    "Mojo", "Mono", "Morph", "Motion", "Nano", "Nebula", "Neon", "Net", "Neural", "Neutron",
    "Nexus", "Night", "Nimbus", "Nitro", "Node", "Noir", "North", "Nova", "Null", "Obsidian",
    "Omega", "Onyx", "Optic", "Orbit", "Origin", "Output", "Oxide", "Ozone", "Pace", "Packet",
    "Paradox", "Parse", "Patch", "Path", "Pattern", "Payload", "Peak", "Phase", "Photon", "Pilot",
    "Ping", "Piston", "Pixel", "Plasma", "Pluto", "Point", "Polar", "Port", "Prism", "Probe",
    "Proxy", "Pulse", "Punk", "Quake", "Quantum", "Quark", "Query", "Quest", "Quick", "Quill",
    "Radar", "Radiant", "Radius", "Raid", "Rain", "Ramp", "Range", "Rapid", "Raven", "Ray",
    "Razor", "Reactor", "Realm", "Reaper", "Rebel", "Recon", "Redux", "Reef", "Reflex", "Relay",
    "Render", "Reno", "Rev", "Rift", "Ripple", "Rise", "Risk", "River", "Rocket", "Rogue",
    "Root", "Rotor", "Route", "Rover", "Ruby", "Rust", "Saga", "Sage", "Saber", "Salt",
    "Satellite", "Saturn", "Scalar", "Scale", "Scan", "Scar", "Schema", "Scope", "Scout", "Scribe",
    "Script", "Scroll", "Sector", "Seed", "Seeker", "Sentry", "Sequel", "Shade", "Shadow", "Shard",
    "Sharp", "Shell", "Shield", "Shift", "Shock", "Short", "Signal", "Silicon", "Silver", "Sim",
    "Sketch", "Slate", "Slice", "Slide", "Slick", "Sling", "Smoke", "Snake", "Snap", "Solar",
    "Solid", "Solo", "Sonic", "Source", "South", "Space", "Span", "Spark", "Spec", "Specter",
    "Spectrum", "Speed", "Sphere", "Spike", "Spiral", "Spirit", "Splice", "Split", "Spore", "Spot",
    "Spring", "Sprint", "Spur", "Spy", "Stack", "Stark", "Static", "Stealth", "Steel", "Stellar",
    "Stem", "Step", "Stereo", "Stitch", "Stock", "Stone", "Storm", "Strafe", "Strand", "Stream",
    "Strobe", "Stroke", "Struct", "Stun", "Style", "Sub", "Summit", "Surge", "Swap", "Swift",
    "Switch", "Sync", "Synth", "System", "Tab", "Tact", "Tag", "Tank", "Tape", "Target",
    "Task", "Tech", "Tempo", "Terra", "Tesla", "Test", "Thread", "Thrust", "Thunder", "Tick",
    "Tide", "Tiger", "Tilt", "Titan", "Token", "Tone", "Torch", "Torque", "Trace", "Track",
    "Trail", "Transit", "Trap", "Trend", "Tribe", "Trick", "Trigger", "Trim", "Trinity", "Trio",
    "Tron", "Tropic", "Trust", "Truth", "Turbo", "Turing", "Tweak", "Twist", "Ultra", "Umbra",
    "Unit", "Unix", "Uplink", "Valor", "Valve", "Vapor", "Vault", "Vector", "Vega", "Veil",
    "Velocity", "Venom", "Venture", "Venus", "Verge", "Vertex", "Vex", "Vibe", "Vice", "Vigor",
    "Viper", "Viral", "Virtue", "Virus", "Vision", "Vital", "Vivid", "Void", "Volt", "Vortex",
    "Vox", "Warp", "Watch", "Wave", "Wax", "Web", "West", "Whisper", "Widget", "Wild",
    "Wind", "Wing", "Wire", "Wisp", "Wolf", "Wraith", "Wren", "Xenon", "Xero", "Xray",
    "Yield", "Zap", "Zeal", "Zen", "Zenith", "Zephyr", "Zero", "Zest", "Zinc", "Zone",
]


def slugify(name: str) -> str:
    """Convert a name to a URL-safe slug (lowercase, alphanumeric, hyphens)."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug or "agent"


def generate_name(used_names: list[str]) -> str:
    """
    Generate a unique agent name from the pool.

    Args:
        used_names: List of names already in use (case-insensitive comparison)

    Returns:
        A unique name from the pool, or a numbered variant if all are taken
    """
    used_lower = {n.lower() for n in used_names}

    # Try to find an unused name from the pool
    available = [n for n in NAMES if n.lower() not in used_lower]

    if available:
        return random.choice(available)

    # All names taken - find a numbered variant
    # Pick a random base name and append numbers until unique
    base = random.choice(NAMES)
    counter = 2
    while f"{base}{counter}".lower() in used_lower:
        counter += 1
    return f"{base}{counter}"


def generate_id(name: str) -> str:
    """Generate an agent ID from a name."""
    return slugify(name)
