from setuptools import find_packages, setup

package_name = 'pos_v1_task'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='place-items-on-shelf',
    maintainer_email='dev@example.com',
    description='Open-loop pick-and-place task node for place-items-on-shelf v1.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pick_and_place = pos_v1_task.pick_and_place:main',
        ],
    },
)
