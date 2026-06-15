from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'mesh_reconstruction'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        ("share/mesh_reconstruction/config", ["config/camera_config.yaml"]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yamato_matsumura',
    maintainer_email='matsumura.yamato@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mesh_node = mesh_reconstruction.mesh:main'
        ],
    },
)
