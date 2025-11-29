{
    init: function(elevators, floors) {
        // Elevator in transit goes to the floor that is the first in their queue (It doesn't dequeue the floor before going there)

        // Strategy flags
        const pickPaxIfClosestWithDetour = true;
        const someStickToTheTop = false;
        const idlePicksNextFromQStrategy = true;
        const idlePicksClosestFromQStrategy = false; // Not so good
        const idlePicksHighestFromQStrategy = false; // Not so good
        const bigElevatorDoesntStopOnWayDown = false; // Not so good

        const topFloor = floors.length - 1;

        const taskQ = [];

        let isItIdle = function(elevator) {
            return elevator.destinationQueue.length == 0 && elevator.destinationDirection() === 'stopped';
        }

        let hasRoom = function(elevator, maxLoadFactor = 0.6) {
            return elevator.loadFactor() <= maxLoadFactor;
        }

        let isBig = function(elevator) {
            // If the big elevator is the on    ly one, treat it as normal
            return elevators.length > 1 && elevator.maxPassengerCount() > 5
        }

        let getDistance = function( elevator, floorNum) {
            return Math.abs( elevator.currentFloor() - floorNum);
        }

        let validateQueue = function( elevator) {
            // Remove queued floors that have no up or down button and are not pressed in the elevator
            for (const floor of elevator.destinationQueue) {
                if ( ! (elevator.getPressedFloors().includes(floor) || floors[floor].buttonStates.up || floors[floor].buttonStates.down)) {
                    elevator.destinationQueue.splice(elevator.destinationQueue.indexOf(floor), 1)
                }
            }
        }

        let validateIndicators = function( elevator) {
            // Make sure the indicators of the elevator show the right direction
            if (isBig(elevator) && bigElevatorDoesntStopOnWayDown) {return;}
            setIndicator(elevator, elevator.destinationDirection())
        }

        let sortByDistanceAndRoomAvailability = function(elevs, floorNum) {
            return elevs.sort((a, b) => {
                const distanceA = getDistance(a, floorNum);
                const distanceB = getDistance(b, floorNum);
                // 1. PRIMARY SORT: Distance

                if (distanceA !== distanceB) {
                    // Sort ascending by distance (closer elevators first)
                    return distanceA - distanceB;
                }

                // 2. TIE-BREAKER: Load Factor
                // If distances are equal, sort ascending by loadFactor (emptier elevators first)
                return a.loadFactor - b.loadFactor;
            });
        };

        let setIndicator = function(elevator, direction) {
            switch (direction) {
                case "up":
                    elevator.goingUpIndicator(true);
                    elevator.goingDownIndicator(false);
                    break;
                case "down":
                    elevator.goingUpIndicator(false);
                    elevator.goingDownIndicator(true);
                    break;
                case "both":
                    elevator.goingUpIndicator(true);
                    elevator.goingDownIndicator(true);
                    break;
                default:
                    elevator.goingUpIndicator(false);
                    elevator.goingDownIndicator(false);
                    break;
            }
        }

        function findBestElevators(direction, callerFloorNum) {
            // Find elevators that go in the same direction, aren't full, and sorted by proximity
            return sortByDistanceAndRoomAvailability(elevators.filter((elevator) => {
                const isIdle = isItIdle(elevator);
                const hasSpace = hasRoom(elevator);

                // --- Checking for Matching Direction ---
                const isMovingUpAndMatches = elevator.goingUpIndicator() && direction === 'up' && elevator.currentFloor() <= callerFloorNum;
                const isMovingDownAndMatches = elevator.goingDownIndicator() && direction === 'down' && elevator.currentFloor() >= callerFloorNum;

                // An elevator is "available" if it's:  
                // 1. Idle (empty queue)
                // OR
                // 2. Has room AND moving in the same direction as the call
                if (bigElevatorDoesntStopOnWayDown) {
                    return hasSpace && ((!isBig(elevator) && (isIdle || isMovingDownAndMatches)) || isMovingUpAndMatches);
                } else {
                    return hasSpace && (isIdle || isMovingUpAndMatches || isMovingDownAndMatches);
                }
            }), callerFloorNum);
        }

        function findCompetingElevators(direction, floorNum) {
            // Find elevators that go in the same direction, aren't full, and sorted by proximity
            return sortByDistanceAndRoomAvailability(elevators.filter((elevator) => {
                const isIdle = isItIdle(elevator);
                const hasSpace = hasRoom(elevator);
                // --- Checking for Matching Direction ---
                const isMovingUpAndMatches = elevator.goingUpIndicator() && direction === 'up';
                const isMovingDownAndMatches = elevator.goingDownIndicator() && direction === 'down';

                // An elevator is "available" if it's:
                // 1. Idle (empty queue)
                // OR
                // 2. Has room AND moving in the same direction as the call
                if (bigElevatorDoesntStopOnWayDown) {
                    return getDistance(elevator, floorNum) <= 2 && hasSpace && ((!isBig(elevator) && (isIdle || isMovingDownAndMatches)) || isMovingUpAndMatches);
                } else {
                    return getDistance(elevator, floorNum) <= 2 && hasSpace && (isIdle || isMovingDownAndMatches || isMovingUpAndMatches);
                }
            }), floorNum);
        }

        // Function to handle the core logic of assigning an elevator
        const handleFloorCall = (floor, direction) => {
            const floorNum = floor.floorNum();
            console.log(`Call at floor ${floorNum} for direction: ${direction}`);

            let options;
            if (pickPaxIfClosestWithDetour) {
                let matchingElevs = elevators.filter((elevator) => (
                    isItIdle(elevator) ||
                    (
                        elevator.loadFactor <= 0.4 && getDistance(elevator, floorNum) <= 3 &&
                        (elevator.goingUpIndicator() && direction === 'up' || elevator.goingDownIndicator() && direction === 'down')
                    )
                ))

                if (someStickToTheTop && floor < floors.length / 2) {
                    // Calls from lower floors won't be serviced by top-stickers
                    matchingElevs = matchingElevs.filter((elev) => elev.id < elevators.length / 2)
                }

                if (bigElevatorDoesntStopOnWayDown && isBig(matchingElevs[0])) {
                    matchingElevs = matchingElevs.filter((elev) => elev.currentFloor() !== topFloor)
                }

                options = sortByDistanceAndRoomAvailability(matchingElevs, floorNum);
            } else {
                options = findBestElevators(floorNum, direction);
            }

            if (options.length) {
                // If idle, go there. Otherwise, the elevator is already going there
                const elev = options[0]

                if (isItIdle(elev)) {
                    elev.goToFloor(floorNum);
                    console.log("Sending there elevator ", options[0].id)
                    elev.currentFloor() < floorNum ? setIndicator(elev, 'up') : setIndicator(elev, 'down')
                } else {
                    console.log("Elevator ", options[0].id, " will pick them up soon")
                }
                console.log(`Elev ${elev.id} queue: ${elev.destinationQueue}`)
            } else {
                // If no suitable elevators available, add to queue
                if (!taskQ.includes(floorNum)) {
                    taskQ.push(floorNum);
                    console.log("Added to Q, pool: ", taskQ)
                }
            }
        };

        /** ELEVATOR LOGIC */
        elevators.forEach(function (elevator, index) {
            // add additional properties to each elevator
            elevator.id = index;
            elevator.subQueue = [] // Used for Big elevators to wait for more passengers

            // Whenever the elevator is idle (has no more queued destinations) ...
            elevator.on("idle", function() {
                console.log(`E ${elevator.id} is idle`)

                if (isBig(elevator) && bigElevatorDoesntStopOnWayDown) {
                    // Big elevator goes straight down without stops
                    setIndicator(elevator, 'none');
                    elevator.goToFloor(0);
                    return;
                }

                setIndicator(elevator, 'both')

                if (someStickToTheTop && taskQ.length == 0 && elevator.id > 2) {
                    setIndicator(elevator, 'up');
                    elevator.goToFloor(topFloor);
                    return;
                }

                while (isItIdle(elevator) && taskQ.length > 0) {
                    console.log(`Elev ${elevator.id} picking next task`)
                    let nextFloor;
                    if (idlePicksNextFromQStrategy) {
                        // Pick the next task from the queue
                        nextFloor = taskQ.shift();
                    } else if (idlePicksClosestFromQStrategy) {
                        // Find the floor within the minimum distance
                        nextFloor = taskQ.reduce((closestFloor, currentFloor) => {
                            const distanceCurrent = getDistance(elevator, currentFloor);
                            const distanceClosest = getDistance(elevator, closestFloor);
                            return distanceCurrent < distanceClosest ? currentFloor : closestFloor;
                        });

                        // Remove the chosen floor from the queue
                        taskQ.splice(taskQ.indexOf(nextFloor), 1);

                    } else if (idlePicksHighestFromQStrategy) {
                        // Find the top-most floor
                        nextFloor = Math.max(...taskQ);
                        taskQ.splice(taskQ.indexOf(nextFloor), 1);
                    }

                    // Check if still needed there
                    if (nextFloor >= 0 && floors[nextFloor].buttonStates['up'] || floors[nextFloor].buttonStates['down']) {
                        elevator.goToFloor(nextFloor);

                        if (nextFloor > elevator.currentFloor() && nextFloor == 8) {
                            setIndicator(elevator, 'up')
                        } else if (nextFloor < elevator.currentFloor() && nextFloor == 0) {
                            setIndicator(elevator, 'down')
                        } else {
                            setIndicator(elevator, 'none')
                        }
                    }
                }
            });

            elevator.on("passing_floor", function(floorNum, direction) {
                console.log(`Elev ${elevator.id} passing floor ${floorNum} queue: ${elevator.destinationQueue}`)
                validateQueue(elevator);
                validateIndicators(elevator);

                const possibleDestinationFloor = direction === 'up' ? floorNum + 1 : floorNum - 1;
                const isDestinationFloorComing = elevator.destinationQueue.includes(possibleDestinationFloor);

                // Check if still need to go there
                if (isDestinationFloorComing && !elevator.getPressedFloors().includes(possibleDestinationFloor) && !(floors[floorNum].buttonStates['up'] || floors[floorNum].buttonStates['down'])) {

                    // If has next stop -> go to the next stop.
                    if (elevator.destinationQueue.length > 1) {
                        console.log(`Skipping floor ${possibleDestinationFloor} as no one is there`)
                        elevator.destinationQueue.splice(elevator.destinationQueue.indexOf(possibleDestinationFloor), 1);
                        elevator.checkDestinationQueue();
                    }
                }

                // If not full and going the same direction - pick them up
                if (elevator.loadFactor() <= 0.6 && floors[floorNum].buttonStates[direction]) {
                    if (isBig(elevator) && direction === 'down' && bigElevatorDoesntStopOnWayDown) {return;}

                    // Check if anothere elevator is closer and will pick them up
                    console.log("E ", elevator.id, " triggered passing check" )
                    const competingElevators = findCompetingElevators(direction, floorNum);

                    console.log("competing: ", competingElevators)

                    if (elevator.id == competingElevators[0].id) {
                        elevator.goToFloor(floorNum, true)
                    }
                }

                // If the floor is the last destination, turn both indicators on
                if (elevator.destinationQueue.length == 1 && elevator.destinationQueue[0] == floorNum && !isBig(elevator)) {
                    setIndicator(elevator, 'both')
                }
            });



            elevator.on("stopped_at_floor", function(floorNum) {
                console.log(`Elev ${elevator.id} queue: ${elevator.destinationQueue}`)

                switch (floorNum) {
                    case 0:
                        setIndicator(elevator, 'up')
                        break;
                    case topFloor:
                        setIndicator(elevator, 'down')
                        break;
                    default:
                        // Check if next stop is up or down and switch the indicator
                        if (elevator.destinationQueue.length) {
                            if (elevator.destinationQueue[0] > floorNum) {
                                setIndicator(elevator, 'up')
                            } else if (elevator.destinationQueue[0] < floorNum) {
                                setIndicator(elevator, 'down')
                            } else {
                                console.log("going anywhere")
                                setIndicator(elevator, 'both')
                            }
                        } else {
                            setIndicator(elevator, 'both')
                        }
                        break;
                }
            })


            elevator.on("floor_button_pressed", function(floorNum) {
                // Note: Pax don't press the floor buttons that are already on (in the queue)
                console.log(`Elev ${elevator.id} queue: ${elevator.destinationQueue}`)
                const curFloor = elevator.currentFloor()

                // Big elevator waits at the 0 floor to fill up
                if (isBig(elevator) && curFloor == 0) {
                    if (hasRoom(elevator, 0.4)) {
                        elevator.subQueue.push(floorNum)
                        return;
                    } else {
                        for (const floor of elevator.subQueue) {
                            if (!elevator.destinationQueue.includes(floor)) {
                                elevator.destinationQueue.push(floor)
                            }

                        }
                    }
                }

                elevator.destinationQueue.push(floorNum)

                if (elevator.destinationQueue.length == 1) {
                    // This pax decides which direction to go
                    floorNum > curFloor ? setIndicator(elevator, 'up') : setIndicator(elevator, 'down')
                }

                else if (elevator.goingUpIndicator()) {
                    // Go to lowest floor in the queue
                    elevator.destinationQueue.sort((a, b) => a - b); // Ascending order
                    setIndicator(elevator, 'up')
                } else if (elevator.goingDownIndicator()){
                    // Go to highest floor in the queue
                    elevator.destinationQueue.sort((a, b) => b - a); // Descending order
                    setIndicator(elevator, 'down')
                } else {
                    console.log("How did this happen?")
                }

                elevator.checkDestinationQueue();
            });
        });

        /** FLOOR BUTTONS LOGIC */
        for (const floor of floors) {
            floor.on("up_button_pressed", function () {
                handleFloorCall(floor, "up");
            });

            floor.on("down_button_pressed", function () {
                handleFloorCall(floor, "down");
            });
        }
    },

        update: function(dt, elevators, floors) {
            // We normally don't need to do anything here
        }
}
