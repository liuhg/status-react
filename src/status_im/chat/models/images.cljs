(ns status-im.chat.models.images
  (:require [re-frame.core :as re-frame]
            [status-im.utils.fx :as fx]
            ["@react-native-community/cameraroll" :as CameraRoll]
            [status-im.utils.types :as types]
            [status-im.ui.components.react :as react]
            [status-im.utils.image-processing :as image-processing]
            [taoensso.timbre :as log]))

(re-frame/reg-fx
 :camera-roll-get-photos
 (fn [num]
   (-> (.getPhotos CameraRoll #js {:first num})
       (.then #(re-frame/dispatch [:on-camera-roll-get-photos (:edges (types/js->clj %))]))
       (.catch #()))))

(fx/defn camera-roll-get-photos
  {:events [:chat.ui/camera-roll-get-photos]}
  [_ num]
  {:camera-roll-get-photos num})

(fx/defn on-camera-roll-get-photos
  {:events [:on-camera-roll-get-photos]}
  [{db :db} photos]
  {:db (assoc db :camera-roll-photos photos)})

(fx/defn cancel-sending-image
  {:events [:chat.ui/cancel-sending-image]}
  [{:keys [db]}]
  (let [current-chat-id (:current-chat-id db)]
    {:db (update-in db [:chats current-chat-id :metadata] dissoc :sending-image)}))

(fx/defn selected-image
  {:events [:chat.ui/selected-image]}
  [{:keys [db]} uri]
  (let [current-chat-id (:current-chat-id db)]
    {:db (assoc-in db [:chats current-chat-id :metadata :sending-image :uri] uri)}))

(re-frame/reg-fx
 :chat-open-image-picker
 (fn []
   (react/show-image-picker
    #(re-frame/dispatch [:chat.ui/selected-image (aget % "path")]))))

(fx/defn chat-open-image-picker
  {:events [:chat.ui/open-image-picker]}
  [_]
  {:chat-open-image-picker nil})

(defn image-resize-and-send [uri]
  (image-processing/resize
   uri
   2000
   2000
   (fn [resized-image]
     (re-frame/dispatch [:chat.ui/send-image (aget resized-image "path")]))
   #(log/error "could not resize image" %)))

(re-frame/reg-fx
 :chat.ui/prepare-and-send-image
 (fn [uri]
   (react/image-get-size
    uri
    (fn [width height]
      (if (> (max width height) 2000)
        (image-resize-and-send uri)
        (re-frame/dispatch [:chat.ui/send-image uri]))))))
