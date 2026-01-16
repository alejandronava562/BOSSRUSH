# Battle Scenes for each boss in BOSSRUSH
# Each scene has a narrative description and 4 choices with associated damage

BATTLE_SCENES = {
    "The Landfill Lord": {
        "descriptions": [
            {
                "scene": "You stand before a towering mountain of trash and filth - The Landfill Lord! Piles of waste surround you like a fortress, emitting toxic fumes. The creature's body is made entirely of discarded items, rattling with each movement. You must find a way to clean up this mess and defeat this lord of environmental destruction!",
                "choices": [
                    {"id": "A", "text": "Use a recycling blaster to sort and neutralize the waste!", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Propose a composting plan to reduce the landfill's power", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Attack with brute force but get overwhelmed by trash", "delta_player": {"hp": -8}, "delta_boss": {"hp": -3}},
                    {"id": "D", "text": "Educate citizens about proper waste management (risky but effective)", "delta_player": {"hp": -3}, "delta_boss": {"hp": -10}}
                ]
            },
            {
                "scene": "The Landfill Lord shifts, and more garbage pours down around you! Old electronics, plastic bags, and broken furniture crash down. You need to act fast before the waste buries you completely!",
                "choices": [
                    {"id": "A", "text": "Dodge left and strike with eco-friendly weaponry", "delta_player": {"hp": -3}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Stand firm and absorb the damage while planning recovery", "delta_player": {"hp": -6}, "delta_boss": {"hp": -2}},
                    {"id": "C", "text": "Activate zero-waste protocol for massive damage", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "D", "text": "Call for help from the community clean-up squad", "delta_player": {"hp": 0}, "delta_boss": {"hp": -5}}
                ]
            }
        ]
    },
    
    "Carbon King": {
        "descriptions": [
            {
                "scene": "Before you stands the Carbon King, a shadowy figure wreathed in thick clouds of pollution! His crown gleams with the light of burning fossil fuels. The air grows thick and toxic as he breathes out waves of greenhouse gases. This is a battle for our planet's future!",
                "choices": [
                    {"id": "A", "text": "Deploy renewable energy shields to block emissions", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Plant massive trees to absorb the carbon quickly", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Challenge him to a debate about climate science", "delta_player": {"hp": -4}, "delta_boss": {"hp": -5}},
                    {"id": "D", "text": "Summon a tornado of solar panels to overwhelm him", "delta_player": {"hp": -3}, "delta_boss": {"hp": -8}}
                ]
            },
            {
                "scene": "The Carbon King unleashes a blast of smog and methane! The greenhouse effect intensifies around you, making it hard to breathe. You see glaciers melting in the distance - his power is growing!",
                "choices": [
                    {"id": "A", "text": "Use electric vehicles as battering rams", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Activate carbon capture technology", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "C", "text": "Take a deep breath and fight through the pollution", "delta_player": {"hp": -7}, "delta_boss": {"hp": -3}},
                    {"id": "D", "text": "Broadcast the truth about climate change worldwide", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}}
                ]
            }
        ]
    },
    
    "Mr. Incinerator": {
        "descriptions": [
            {
                "scene": "Flames erupt around you as Mr. Incinerator emerges from a burning inferno! His body is literally on fire, and ash rains down from above. He represents the toxic practice of burning waste to dispose of it. Can you extinguish his power?",
                "choices": [
                    {"id": "A", "text": "Douse him with a water shield made from conserved resources", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Propose waste-to-energy alternatives", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Jump through the flames to reach him directly", "delta_player": {"hp": -9}, "delta_boss": {"hp": -4}},
                    {"id": "D", "text": "Use non-toxic decomposition magic to neutralize emissions", "delta_player": {"hp": -3}, "delta_boss": {"hp": -9}}
                ]
            },
            {
                "scene": "Mr. Incinerator roars and creates a wall of flames between you two! The heat is unbearable. Toxic fumes are filling the area - you must act quickly!",
                "choices": [
                    {"id": "A", "text": "Break through with a recycling hammer", "delta_player": {"hp": -5}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Counter with biodegradable solutions", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "C", "text": "Call for fire safety inspectors to shut him down", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "D", "text": "Meditate to build resistance to the heat", "delta_player": {"hp": -2}, "delta_boss": {"hp": -2}}
                ]
            }
        ]
    },
    
    "Tree Slayer": {
        "descriptions": [
            {
                "scene": "A grotesque figure wielding a massive chainsaw emerges from the forest - the Tree Slayer! The ground trembles with each step, and the sound of chainsaws echoes in the distance. Behind him lies a trail of deforestation and destruction. The forest itself seems to be crying for help!",
                "choices": [
                    {"id": "A", "text": "Plant new trees as shields while you fight", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Appeal to his conscience about forest ecosystems", "delta_player": {"hp": -1}, "delta_boss": {"hp": -5}},
                    {"id": "C", "text": "Counter his chainsaw with a wooden sword", "delta_player": {"hp": -7}, "delta_boss": {"hp": -6}},
                    {"id": "D", "text": "Summon forest spirits to protect and heal nature", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}}
                ]
            },
            {
                "scene": "The Tree Slayer swings his chainsaw wildly! The forest quakes and splinters fly everywhere. You can see endangered animals fleeing for their lives. This villain must be stopped before the entire forest is gone!",
                "choices": [
                    {"id": "A", "text": "Hack off his chainsaw with sustainable timber", "delta_player": {"hp": -4}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Establish a nature sanctuary to trap him", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Challenge him to replant trees to undo his damage", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Attack with raw force but risk more damage", "delta_player": {"hp": -8}, "delta_boss": {"hp": -4}}
                ]
            }
        ]
    },
    
    "Plastic Pirate": {
        "descriptions": [
            {
                "scene": "A pirate covered head to toe in plastic debris emerges from an ocean of trash! The Plastic Pirate wields hooks made of discarded plastic bags, and a treasure chest overflowing with single-use containers. The seas around him are choked with pollution. This buccaneer of waste must be defeated!",
                "choices": [
                    {"id": "A", "text": "Attack with a reusable container cannon", "delta_player": {"hp": -3}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Educate about the dangers of microplastics", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Use ocean currents to wash away his plastic armor", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "D", "text": "Engage in direct combat but get tangled in plastic", "delta_player": {"hp": -8}, "delta_boss": {"hp": -3}}
                ]
            },
            {
                "scene": "The Plastic Pirate throws nets of tangled plastic at you! Fish and sea creatures are caught in the crossfire. The ocean is turning into a graveyard of plastic waste. You must act to save the marine life!",
                "choices": [
                    {"id": "A", "text": "Free the creatures and gain their help", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Use biodegradable nets to counter his attack", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Push him out to sea with a tidal wave", "delta_player": {"hp": -4}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Dodge and recover health with ocean breeze", "delta_player": {"hp": 1}, "delta_boss": {"hp": -3}}
                ]
            }
        ]
    },
    
    "Water Waster": {
        "descriptions": [
            {
                "scene": "A tidal wave crashes as the Water Waster appears, surrounded by endless streams of wasted water! He leaves rivers running in every direction with reckless abandon. Fountains spray uselessly while nearby villages have no clean water to drink. This must stop!",
                "choices": [
                    {"id": "A", "text": "Install conservation pumps to redirect the flow", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Show him villages suffering from water scarcity", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Swim against the current to reach him", "delta_player": {"hp": -6}, "delta_boss": {"hp": -5}},
                    {"id": "D", "text": "Summon drought spirits to dry up his power", "delta_player": {"hp": -3}, "delta_boss": {"hp": -9}}
                ]
            },
            {
                "scene": "The Water Waster creates a tsunami of waste water rushing toward you! You can see pollutants swirling in the current. Rainfall collection systems and wells lie in its path. You need to stop this flood of destruction!",
                "choices": [
                    {"id": "A", "text": "Build rain barriers to filter and collect water", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Attack his control over water sources", "delta_player": {"hp": -4}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Teach him about aquifer depletion and water cycles", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Let the wave hit and absorb the impact", "delta_player": {"hp": -7}, "delta_boss": {"hp": -2}}
                ]
            }
        ]
    },
    
    "Energy Eater": {
        "descriptions": [
            {
                "scene": "The Energy Eater materializes as a massive creature constantly devouring power - electricity crackles across its skin, and light bulbs explode around it! This villain represents endless consumption and energy waste. Power plants shut down in its wake. Only sustainable power can defeat it!",
                "choices": [
                    {"id": "A", "text": "Power up with solar and wind energy attacks", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Show the benefits of energy efficiency", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Strike quickly before your stamina drains", "delta_player": {"hp": -5}, "delta_boss": {"hp": -6}},
                    {"id": "D", "text": "Overload circuits to confuse and damage it", "delta_player": {"hp": -3}, "delta_boss": {"hp": -8}}
                ]
            },
            {
                "scene": "The Energy Eater opens its mouth and pulls energy from everything around you! Lights flicker, batteries die, and darkness spreads. Your own power is being drained. This is a critical moment - act now or lose everything!",
                "choices": [
                    {"id": "A", "text": "Channel stored renewable energy for a mega attack", "delta_player": {"hp": -2}, "delta_boss": {"hp": -11}},
                    {"id": "B", "text": "Use LED lights and smart grids to counter it", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Move to an off-grid location to escape the drain", "delta_player": {"hp": -3}, "delta_boss": {"hp": -3}},
                    {"id": "D", "text": "Fight through the energy drain with pure will", "delta_player": {"hp": -6}, "delta_boss": {"hp": -5}}
                ]
            }
        ]
    },
    
    "Air Polluter": {
        "descriptions": [
            {
                "scene": "A sinister figure emerges from a cloud of smog and toxic fumes - the Air Polluter! Car exhaust forms a cloak around it, and the sky turns gray wherever it goes. Children cough, lungs burn, and breathing becomes difficult. This villain suffocates our atmosphere!",
                "choices": [
                    {"id": "A", "text": "Release clean air purification waves", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Promote electric vehicles and public transit", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Push through the smog with a gas mask", "delta_player": {"hp": -5}, "delta_boss": {"hp": -5}},
                    {"id": "D", "text": "Plant massive tree barriers to filter the air", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}}
                ]
            },
            {
                "scene": "The Air Polluter expands, filling the entire battlefield with noxious gas! Visibility drops to almost nothing. You can barely see your hand in front of your face. Asthmatics around you struggle to breathe. You must clear this toxic cloud!",
                "choices": [
                    {"id": "A", "text": "Summon winds to blow away all pollution", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Activate industrial air filter technology", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "C", "text": "Create oxygen bubbles to survive the poison", "delta_player": {"hp": -4}, "delta_boss": {"hp": -4}},
                    {"id": "D", "text": "Advance blindly through the smog", "delta_player": {"hp": -7}, "delta_boss": {"hp": -3}}
                ]
            }
        ]
    },
    
    "Soil Spoiler": {
        "descriptions": [
            {
                "scene": "From cracked, poisoned earth rises the Soil Spoiler - a grotesque creature made of contaminated dirt and toxic chemicals! The ground beneath your feet turns black and barren. Plants wither instantly. This villain destroys the very foundation of life!",
                "choices": [
                    {"id": "A", "text": "Use organic compost to heal and strengthen soil", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Teach proper pesticide disposal methods", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Fight on solid ground for stability bonus", "delta_player": {"hp": -3}, "delta_boss": {"hp": -5}},
                    {"id": "D", "text": "Restore biodiversity through regenerative farming", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}}
                ]
            },
            {
                "scene": "The Soil Spoiler spreads contamination across the land like a plague! Farmers watch helplessly as their crops die. The earth itself seems to cry out in pain. You must stop this contamination before it's too late!",
                "choices": [
                    {"id": "A", "text": "Deploy mycoremediation (healing mushrooms)", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Use earthworms and microorganisms to fight back", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Build barriers with clean topsoil", "delta_player": {"hp": -3}, "delta_boss": {"hp": -6}},
                    {"id": "D", "text": "Attack directly, contaminating yourself", "delta_player": {"hp": -8}, "delta_boss": {"hp": -4}}
                ]
            }
        ]
    },
    
    "Wildlife Wrecker": {
        "descriptions": [
            {
                "scene": "A terrible creature made of shattered ecosystems emerges - the Wildlife Wrecker! Species vanish in its shadow, and habitats crumble to dust. The desperate cries of endangered animals echo around you. Biodiversity is collapsing with every breath it takes!",
                "choices": [
                    {"id": "A", "text": "Establish protected nature reserves as shields", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Raise awareness about endangered species", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Call animal allies to fight alongside you", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Restore lost habitats and ecosystems", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}}
                ]
            },
            {
                "scene": "The Wildlife Wrecker roars and causes mass extinction events! Animals disappear from existence. The food chain collapses around you. Ecosystems that took millennia to build are destroyed in seconds. This must be stopped now!",
                "choices": [
                    {"id": "A", "text": "Release conservation DNA to revitalize species", "delta_player": {"hp": -2}, "delta_boss": {"hp": -11}},
                    {"id": "B", "text": "Build global wildlife corridors to reconnect habitats", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Fight ferociously to protect remaining animals", "delta_player": {"hp": -5}, "delta_boss": {"hp": -7}},
                    {"id": "D", "text": "Show the beauty and value of biodiversity", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}}
                ]
            }
        ]
    },
    
    "Ocean Obliterator": {
        "descriptions": [
            {
                "scene": "From the depths of a dying ocean emerges the Ocean Obliterator - a colossal terror wrapped in fishing nets and oil slicks! Coral bleaches, fish populations collapse, and the sea itself becomes a wasteland. The oceans are suffocating under human greed!",
                "choices": [
                    {"id": "A", "text": "Deploy marine protected areas as defenses", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Clean up ocean plastic and restore reefs", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Stop illegal overfishing operations", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Swim through pollution to reach it directly", "delta_player": {"hp": -7}, "delta_boss": {"hp": -5}}
                ]
            },
            {
                "scene": "The Ocean Obliterator creates massive waves of pollution and dead zones! Whales beach themselves, and jellyfish blooms choke the ocean. Islands are sinking from the chaos. The very existence of marine life hangs in the balance!",
                "choices": [
                    {"id": "A", "text": "Clean ocean currents to reverse destruction", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Ban destructive fishing and drilling practices", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Create artificial reefs to restore ecosystems", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Call upon dolphins and whales as allies", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}}
                ]
            }
        ]
    },
    
    "Climate Conqueror": {
        "descriptions": [
            {
                "scene": "The ultimate environmental villain appears - the Climate Conqueror! Floods, hurricanes, wildfires, and droughts swirl around it in chaos. Temperatures spike dangerously, ice caps melt, and sea levels rise. This is the final embodiment of climate chaos. The fate of our world rests on this battle!",
                "choices": [
                    {"id": "A", "text": "Achieve net-zero emissions for a powerful strike", "delta_player": {"hp": -2}, "delta_boss": {"hp": -11}},
                    {"id": "B", "text": "Plant forests and restore carbon sinks", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Switch the world to renewable energy", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}},
                    {"id": "D", "text": "Make a desperate but risky gambit", "delta_player": {"hp": -8}, "delta_boss": {"hp": -6}}
                ]
            },
            {
                "scene": "The Climate Conqueror unleashes all its fury at once! Hurricanes spin, wildfires rage, floods rise, and droughts parch the earth simultaneously! This is the ultimate test - will you save our planet?",
                "choices": [
                    {"id": "A", "text": "Mobilize global climate action and unity", "delta_player": {"hp": -1}, "delta_boss": {"hp": -12}},
                    {"id": "B", "text": "Invest in renewable energy infrastructure worldwide", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}},
                    {"id": "C", "text": "Inspire behavior change in every person on Earth", "delta_player": {"hp": -1}, "delta_boss": {"hp": -11}},
                    {"id": "D", "text": "Use everything you've learned in previous battles", "delta_player": {"hp": -3}, "delta_boss": {"hp": -9}}
                ]
            }
        ]
    },
    
    "Garbage Goblin": {
        "descriptions": [
            {
                "scene": "A mischievous yet sinister creature scurries forward - the Garbage Goblin! Litter swirls around it in a tornado of carelessness. It leaves trails of trash wherever it goes, cackling as it pollutes streets and parks. Every piece of litter strengthens this creature!",
                "choices": [
                    {"id": "A", "text": "Launch a city-wide cleanup campaign", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Install smart trash bins to stop illegal dumping", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Chase and catch the goblin before it spreads trash", "delta_player": {"hp": -5}, "delta_boss": {"hp": -5}},
                    {"id": "D", "text": "Educate communities about proper waste disposal", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}}
                ]
            },
            {
                "scene": "The Garbage Goblin multiplies into dozens of smaller goblins, each scattering trash everywhere! Parks become dumps, beaches become landfills, and streets turn into garbage zones. The goblin army is overwhelming - you need a bigger strategy!",
                "choices": [
                    {"id": "A", "text": "Inspire volunteers for a massive cleanup", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Implement strict fines for littering", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Use recycling technology to neutralize all trash", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Confront each goblin individually (exhausting)", "delta_player": {"hp": -8}, "delta_boss": {"hp": -6}}
                ]
            }
        ]
    },
    
    "Fossil Fuel Fiend": {
        "descriptions": [
            {
                "scene": "A demonic figure emerges from clouds of smoke and petroleum fumes - the Fossil Fuel Fiend! Its body drips with crude oil, and it's powered by an endless hunger for coal, gas, and ancient energy sources. The addiction to fossil fuels has given it immense power!",
                "choices": [
                    {"id": "A", "text": "Transition infrastructure to renewable energy", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Expose the hidden costs of fossil fuels", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Disable oil rigs and coal mines with EMP attacks", "delta_player": {"hp": -4}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Invest in alternative energy research", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}}
                ]
            },
            {
                "scene": "The Fossil Fuel Fiend ignites in a massive explosion of petroleum energy! The blast scorches everything, and an enormous fireball engulfs the battlefield. Oil spills flow like rivers, coating everything in toxic sludge. This creature is at peak power!",
                "choices": [
                    {"id": "A", "text": "Deploy solar and wind weapons for maximum damage", "delta_player": {"hp": -2}, "delta_boss": {"hp": -11}},
                    {"id": "B", "text": "Switch entire nations to clean energy", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "C", "text": "Use geothermal energy to absorb the heat", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "D", "text": "Endure the blast and counterattack", "delta_player": {"hp": -6}, "delta_boss": {"hp": -6}}
                ]
            }
        ]
    },
    
    "Chemical Crusher": {
        "descriptions": [
            {
                "scene": "A toxic monster rises from a sea of hazardous waste - the Chemical Crusher! Its body oozes with dangerous substances, and radioactive energy pulses from its core. Industrial waste and abandoned chemicals fuel its existence. This creature is a walking environmental disaster!",
                "choices": [
                    {"id": "A", "text": "Deploy hazmat technology to neutralize toxins", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Enforce strict chemical disposal regulations", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Destroy chemical storage facilities it's protecting", "delta_player": {"hp": -4}, "delta_boss": {"hp": -7}},
                    {"id": "D", "text": "Use chelation therapy to bind its toxic power", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}}
                ]
            },
            {
                "scene": "The Chemical Crusher explodes in a cloud of noxious gas and contaminated liquid! The battlefield becomes a toxic swamp. Acid pools form, and poisonous fumes fill the air. Anyone breathing normally will be overcome. Time is running out!",
                "choices": [
                    {"id": "A", "text": "Use advanced filtration to survive and strike", "delta_player": {"hp": -1}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Neutralize all hazardous chemicals", "delta_player": {"hp": -2}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Call in bioremediation specialists", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Fight through the poison to reach the core", "delta_player": {"hp": -7}, "delta_boss": {"hp": -5}}
                ]
            }
        ]
    },
    
    "Noise Nemesis": {
        "descriptions": [
            {
                "scene": "A deafening creature materializes - the Noise Nemesis! It's a cacophony of sound pollution made manifest - car horns, jackhammers, jet engines, and sirens all fused into one ear-shattering form. The constant noise disorients you and damages your hearing. Silence and peace are losing!",
                "choices": [
                    {"id": "A", "text": "Create sound barriers to protect the environment", "delta_player": {"hp": -2}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Promote quiet zones and noise regulations", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Use earplugs and shield yourself", "delta_player": {"hp": -3}, "delta_boss": {"hp": -4}},
                    {"id": "D", "text": "Play soothing sounds to counter the chaos", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}}
                ]
            },
            {
                "scene": "The Noise Nemesis reaches a deafening crescendo! The soundwaves are so powerful they cause physical damage. Animals flee in terror, and humans cover their ears in pain. The very ground shakes from the acoustic assault!",
                "choices": [
                    {"id": "A", "text": "Generate white noise to cancel its frequencies", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "B", "text": "Enforce strict noise control enforcement", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "C", "text": "Use soundproof armor to resist damage", "delta_player": {"hp": -1}, "delta_boss": {"hp": -3}},
                    {"id": "D", "text": "Plant trees to create natural sound barriers", "delta_player": {"hp": -2}, "delta_boss": {"hp": -6}}
                ]
            }
        ]
    },
    
    "Light Looter": {
        "descriptions": [
            {
                "scene": "A shadowy creature wreathed in artificial light emerges - the Light Looter! Streetlights flicker wildly, and the stars disappear as it spreads light pollution everywhere. Birds lose their way, ecosystems fall into chaos, and the beauty of the night sky vanishes. Darkness and beauty are fading!",
                "choices": [
                    {"id": "A", "text": "Switch to low-energy LED lighting", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Protect dark sky reserves from light invasion", "delta_player": {"hp": -1}, "delta_boss": {"hp": -6}},
                    {"id": "C", "text": "Turn off unnecessary lights to weaken it", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Fight in the darkness to regain your sight", "delta_player": {"hp": -4}, "delta_boss": {"hp": -5}}
                ]
            },
            {
                "scene": "The Light Looter bathes the entire world in blinding artificial light! Night becomes day, and day becomes unbearable. Birds are confused and exhausted, nocturnal animals lose their habitats, and human sleep cycles are disrupted. The natural order is being destroyed!",
                "choices": [
                    {"id": "A", "text": "Designate dark sky sanctuaries", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "B", "text": "Use smart lighting to reduce unnecessary illumination", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "C", "text": "Create natural darkness zones for wildlife", "delta_player": {"hp": -2}, "delta_boss": {"hp": -8}},
                    {"id": "D", "text": "Overcome the blindness and attack", "delta_player": {"hp": -5}, "delta_boss": {"hp": -6}}
                ]
            }
        ]
    },
    
    "Forest Fumbler": {
        "descriptions": [
            {
                "scene": "A clumsy yet destructive creature stumbles forward - the Forest Fumbler! Despite its clumsiness, it destroys everything in its path. Habitats crumble, ecosystems collapse, and the delicate balance of forests is shattered. Carelessness and ignorance fuel its destruction!",
                "choices": [
                    {"id": "A", "text": "Teach forest management and conservation", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "B", "text": "Restore damaged habitats with precision care", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "C", "text": "Guide the fumbler away from sensitive areas", "delta_player": {"hp": -2}, "delta_boss": {"hp": -5}},
                    {"id": "D", "text": "Use controlled burns to manage forest health", "delta_player": {"hp": -3}, "delta_boss": {"hp": -7}}
                ]
            },
            {
                "scene": "The Forest Fumbler goes into a frenzy, accidentally destroying ancient old-growth forests! Trees centuries old fall in seconds. Endangered species lose their only homes. The damage is so extensive it feels irreversible. You must stop this rampage!",
                "choices": [
                    {"id": "A", "text": "Plant millions of trees to restore the forest", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Enforce strict protected forest zones", "delta_player": {"hp": -1}, "delta_boss": {"hp": -8}},
                    {"id": "C", "text": "Educate about the value of old-growth forests", "delta_player": {"hp": -1}, "delta_boss": {"hp": -7}},
                    {"id": "D", "text": "Physically restrain the fumbler", "delta_player": {"hp": -6}, "delta_boss": {"hp": -6}}
                ]
            }
        ]
    },
    
    "Chief Habitat Wrecker": {
        "descriptions": [
            {
                "scene": "The final environmental boss emerges - the Chief Habitat Wrecker! This is the leader of all destruction, the mastermind behind habitat loss. Its very presence causes ecosystems to collapse. Entire species go extinct in its shadow. This is the ultimate embodiment of environmental devastation!",
                "choices": [
                    {"id": "A", "text": "Create a global network of protected habitats", "delta_player": {"hp": -2}, "delta_boss": {"hp": -10}},
                    {"id": "B", "text": "Restore connectivity between fragmented ecosystems", "delta_player": {"hp": -1}, "delta_boss": {"hp": -9}},
                    {"id": "C", "text": "Rally all previous boss allies to fight together", "delta_player": {"hp": -1}, "delta_boss": {"hp": -11}},
                    {"id": "D", "text": "Sacrifice your own health for maximum damage", "delta_player": {"hp": -8}, "delta_boss": {"hp": -8}}
                ]
            },
            {
                "scene": "The Chief Habitat Wrecker unleashes a final wave of destruction across all ecosystems simultaneously! Rainforests burn, coral reefs bleach, deserts expand, and mountains crumble. This is the end game - save our planet or lose everything!",
                "choices": [
                    {"id": "A", "text": "Unite humanity to protect all remaining habitats", "delta_player": {"hp": -1}, "delta_boss": {"hp": -12}},
                    {"id": "B", "text": "Restore every damaged ecosystem with combined effort", "delta_player": {"hp": -2}, "delta_boss": {"hp": -11}},
                    {"id": "C", "text": "Inspire global environmental revolution", "delta_player": {"hp": -1}, "delta_boss": {"hp": -13}},
                    {"id": "D", "text": "Use all learnings from every previous battle", "delta_player": {"hp": -3}, "delta_boss": {"hp": -10}}
                ]
            }
        ]
    }
}

def get_battle_scene(boss_name, scene_index=0):
    """
    Get a specific battle scene for a boss.
    
    Args:
        boss_name: Name of the boss
        scene_index: Which description to use (0 or 1, typically alternates during battle)
    
    Returns:
        Dictionary with 'scene' and 'choices' keys
    """
    if boss_name not in BATTLE_SCENES:
        return None
    
    scenes = BATTLE_SCENES[boss_name]["descriptions"]
    scene = scenes[scene_index % len(scenes)]
    
    return {
        "scene": scene["scene"],
        "choices": scene["choices"]
    }
