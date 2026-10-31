from setuptools import setup, find_packages

setup(
    name="hyprland-config-manager",
    version="1.0.0",
    description="Modern graphical configuration manager for Hyprland on Arch Linux",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "hyprland-config-manager=hyprconf_manager.main:main",
        ],
    },
    data_files=[
        ("share/applications", ["data/hyprland-config-manager.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["data/icons/hicolor/scalable/apps/hyprland-config-manager.svg"]),
    ],
    classifiers=[
        "Environment :: X11 Applications :: GTK",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: Desktop Environment",
    ],
)
