import requests
import json
import time

class Orchestrator(object):
    def __init__(self, conveyor, robot, host_url):
        self.zones = {"1": "-1",
                      "2": "-1",
                      "3": "-1",
                      "4": "-1",
                      "5": "-1"}
        self.conveyor = conveyor
        self.robot = robot
        self.host_url = host_url
        self.events_conveyor = ["Z1_Changed",
                                "Z2_Changed",
                                "Z3_Changed",
                                "Z4_Changed",
                                "Z5_Changed"]
        self.events_robot = "DrawEndExecution"
        self.finish_task = False
        self.pallets = {}

        self.order_list = []
        self.draw_one = -1
        self.calibrate()

        for i in range(5):
            self.update_status_zone(str(i + 1))

    def update_status_zone(self, zone_id):
        url = f"{self.conveyor}/rest/services/Z{zone_id}"
        result = requests.post(url, json={})
        # if result.status_code != 202:
        #     print(f"Fail to get status {str(result.status_code)}")
        #     print(f"status of {zone_id} is {self.zones[zone_id]}")
        #     return

        content = json.loads(result.content)
        pallet_id = content['PalletID']

        self.zones[zone_id] = pallet_id
        print(f"{zone_id} status : {self.zones[zone_id]}")
        return

    def trans_zone(self, from_pallet, to_pallet):

        url = f"{self.conveyor}/rest/services/TransZone{from_pallet}{to_pallet}"

        result = requests.post(url, json={"destUrl": self.host_url})

        if result.status_code == 202:
            print("Done transferring")
        else:
            print(f"Fail to transfer {str(result.status_code)}")
        return

    def conveyor_event_z1(self, pallet_id):
        # leaving
        if pallet_id == "-1":
            print(f"Z1 leaving")
            self.zones["1"] = "-1"
        # arriving
        else:
            print(f"Z1 arrive")
            self.zones["1"] = pallet_id

            self.pallets[str(pallet_id)] = Pallet(str(pallet_id))
            while True:
                if len(self.order_list) != 0:
                    self.pallets[str(pallet_id)].add_order(self.order_list[0])
                    self.order_list.pop(0)
                    if self.zones["2"] == "-1":
                        self.trans_zone("1", "2")

                    elif self.zones["4"] == "-1":
                        self.trans_zone("1", "4")
                    break
                time.sleep(1)


    def conveyor_event_z2(self, pallet_id):
        # leaving
        if pallet_id == "-1":
            print(f"Z2 leaving")
            self.zones["2"] = "-1"

            if self.zones["1"] != "-1":
                self.trans_zone("1", "2")
        # arrive
        else:
            print(f"Z2 arrive")
            self.zones["2"] = pallet_id

            if self.zones["3"] == "-1":
                self.trans_zone("2", "3")

    def conveyor_event_z3(self, pallet_id):
        # leaving
        if pallet_id == "-1":
            print(f"Z3 leaving")
            self.zones["3"] = "-1"
            if self.zones["2"] != "-1":
                self.trans_zone("2", "3")
        # arrive
        else:
            print(f"Z3 arrive")
            self.zones["3"] = pallet_id
            # TODO: add action when pallet arrives drawing area
            self.start_draw(pallet_id)

    def conveyor_event_z4(self, pallet_id):
        # leaving
        if pallet_id == "-1":
            print(f"Z4 leaving")
            self.zones["4"] = "-1"

            if self.zones["1"] != "-1" and self.zones['2'] != "-1":
                self.trans_zone("1", "4")
        # arrive
        else:
            print(f"Z4 arrive")
            self.zones["4"] = pallet_id

            if self.zones["5"] == "-1":
                self.trans_zone("4", "5")

    def conveyor_event_z5(self, pallet_id):
        # leaving
        if pallet_id == "-1":
            print(f"Z5 leaving")
            self.zones['5'] = "-1"

            # TODO: more condition, robot has to finish draw before move to zone 5
            if self.zones["3"] != "-1" and self.finish_task:
                self.trans_zone("3", "5")
                self.finish_task = False

            elif self.zones["4"]:
                self.trans_zone("4", "5")
        # arrive
        else:
            print(f"Z5 arrive")
            self.zones["5"] = pallet_id

    def start_draw(self, pallet_id):
        num_draw = self.pallets[str(pallet_id)].draw_num
        list_draw = self.pallets[str(pallet_id)].order
        print("start draw")
        # self.draw_one = 0
        # i = 0
        # while True:
        #     if self.draw_one == i:
        #         if i < num_draw:
        url = f"{self.robot}/rest/services/{list_draw}"
        print(url)
        result = requests.post(url, json={"destUrl": self.host_url})
        print("Sending drawing")
        if result.status_code != 202:
            print(f"Unable to draw {str(result.status_code)}")
            return False, "Request error!"
                    # self.finish_task = False
                    # i += 1
                # else:
        # self.finish_task = True
                    # break
            # time.sleep(0.5)
        return True, "Draw completed!"

    def finish_draw(self):
        print("Finish draw")
        # self.draw_one += 1
        self.finish_task = True
        # if self.finish_task:
        time.sleep(1)
        print("Done Draw all!!!")
        if self.zones["5"] == "-1":
            self.trans_zone("3", "5")
            self.finish_task = False
        # else:
        #     print(f"Not done {self.draw_one}! More Draw need to finish ...")

    def event_handler(self, json_):
        print(json_)
        for i in range(5):
            self.update_status_zone(str(i + 1))

        if json_ == {}:
            return False, "Nothing to process"
        event_id = json_["id"]

        print(f"Receive signal from {event_id} ")
        if event_id == "Z1_Changed":
            self.conveyor_event_z1(json_["payload"]["PalletID"])
        elif event_id == "Z2_Changed":
            self.conveyor_event_z2(json_["payload"]["PalletID"])
        elif event_id == "Z3_Changed":
            self.conveyor_event_z3(json_["payload"]["PalletID"])
        elif event_id == "Z4_Changed":
            self.conveyor_event_z4(json_["payload"]["PalletID"])
        elif event_id == "Z5_Changed":
            self.conveyor_event_z5(json_["payload"]["PalletID"])
        elif event_id == "DrawEndExecution":

            self.finish_draw()
        else:
            print(f"Other Event: {event_id}")
        return True, "Success Receive"

    def subscribe_notif(self):
        for i in self.events_conveyor:
            url = f"{self.conveyor}/rest/events/{i}/notifs"

            result = requests.post(url, json={"destUrl": self.host_url})

            if result.status_code != 200:
                print("Error conveyor subscribe: " + str(result.status_code))
        return True, "Sub all conveyor events"

    def sub_robot(self):

        url = f"{self.robot}/rest/events/{self.events_robot}/notifs"

        result = requests.post(url, json={"destUrl": self.host_url})

        if result.status_code != 200:
            print("Error robot subscribe: " + str(result.status_code))
        return True, "Sub robot events"


    def unsubscribe_notif(self):
        for i in self.events_conveyor:
            url = f"{self.conveyor}/rest/events/{i}/notifs"

            # TODO: check how many subscribers (from service ???)
            result = requests.delete(url)

            if result.status_code != 200:
                print("Error conveyor del sub: " + str(result.status_code))
        return True, "Unsub all conveyor events"

    def unsub_robot(self):
        url = f"{self.robot}/rest/events/{self.events_robot}/notifs"

        result = requests.delete(url)

        if result.status_code != 200:
            print("Error robot del sub: " + str(result.status_code))

        return True, "Unsub all robot events"


    def calibrate(self):
        url = f"{self.robot}/rest/services/Calibrate"
        result = requests.post(url, json={})

        if result.status_code == 202:
            print("Done calibrate")
        else:
            print(f"Fail calibrate {str(result.status_code)}")

        return True, "Calib Robot"

    def store_order(self, order):
        if len(order) != 0:
            self.order_list.append(order)
        return True, "Add order to order_list"



class Pallet:
    def __init__(self,id):
        self.palletID = id
        self.order = ""
        self.draw_num = 0

    def add_order(self, order):
        self.order = order
        self.draw_num = len(order)
