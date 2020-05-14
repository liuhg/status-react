(ns status-im.ui.screens.chat.image.views
  (:require-macros [status-im.utils.views :refer [defview letsubs]])
  (:require [status-im.ui.components.react :as react]
            [status-im.utils.platform :as platform]
            [re-frame.core :as re-frame]
            [status-im.ui.components.colors :as colors]
            [status-im.ui.components.animation :as anim]
            [status-im.ui.screens.chat.image.styles :as styles]
            [status-im.utils.utils :as utils]
            [status-im.i18n :as i18n]
            [status-im.ui.components.icons.vector-icons :as icons]
            [status-im.ui.components.camera :as camera]
            [reagent.core :as reagent]
            [taoensso.timbre :as log]))

(defn show-panel-anim
  [bottom-anim-value alpha-value]
  (anim/start
   (anim/parallel
    [(anim/spring bottom-anim-value {:toValue         0
                                     :useNativeDriver true})
     (anim/timing alpha-value {:toValue         1
                               :duration        500
                               :useNativeDriver true})])))

(defn image-captured [^js data]
  (re-frame/dispatch [:chat.ui/selected-image (.-uri data)])
  (re-frame/dispatch [:navigate-back]))

(defn camera-permissions []
  [react/view {:flex 1 :justify-content :center :align-items :center}
   [react/view {:width       128 :height 208 :background-color "rgba(0, 0, 0, 0.86)" :border-radius 4
                :align-items :center :justify-content :center}
    [icons/icon :camera-permission {:color colors/gray}]
    [react/text {:style {:margin-top        8 :color colors/gray :font-size 12
                         :margin-horizontal 8 :text-align :center}}
     "Give permission\nto access camera"]]])

(defn camera-permissions-fn [obj]
  (when-not (= "READY" (.-status obj))
    (reagent/as-element [camera-permissions])))

(defn image-picker []
  (let [camera-ref (reagent/atom nil)
        front?     (reagent/atom true)]
    (fn []
      [react/view {:flex 1}
       [camera/camera
        {:style          {:flex 1}
         :captureQuality "480p"
         :type           (if @front? "front" "back")
         :ref            #(reset! camera-ref %)
         :captureAudio   false}
        camera-permissions-fn]
       [react/view {:position :absolute :bottom 0 :left 0 :right 0}
        [react/safe-area-view {:style {:flex 1 :justify-content :flex-end}}
         [react/view {:flex-direction :row :justify-content :space-between :align-items :center
                      :padding        16}
          [react/touchable-highlight
           {:on-press #(swap! front? not)}
           [react/view {:width       48 :height 48 :border-radius 44 :background-color "rgba(0, 0, 0, 0.86)"
                        :align-items :center :justify-content :center}
            [icons/icon :rotate-camera {:color colors/white}]]]
          [react/touchable-highlight
           {:on-press (fn []
                        (let [^js camera @camera-ref]
                          (-> (.takePictureAsync camera)
                              (.then image-captured)
                              (.catch #(log/debug "Error capturing image: " %)))))}
           [react/view {:width        73 :height 73 :border-radius 70 :background-color "rgba(0, 0, 0, 0.86)"
                        :border-width 4 :border-color colors/white}]]
          ;;TODO implement
          [react/view {:width 48 :height 48}]
          #_[react/view {:width       48 :height 48 :border-radius 44 :background-color "rgba(0, 0, 0, 0.86)"
                         :align-items :center :justify-content :center}
             [icons/icon :flash {:color colors/white}]]]
         [react/touchable-highlight
          {:style    {:align-self :center}
           :on-press #(re-frame/dispatch [:navigate-back])}
          [react/view {:width       90 :height 40 :border-radius 44 :background-color "rgba(0, 0, 0, 0.86)"
                       :align-items :center :justify-content :center}
           [react/text {:style {:color colors/white}}
            "Close"]]]]]])))

(defn button [images-showing?]
  [react/touchable-highlight
   {:on-press
                         (fn [_]
                           (re-frame/dispatch [:chat.ui/set-chat-ui-props
                                               {:input-bottom-sheet (when-not images-showing? :images)}])
                           (when-not platform/desktop? (js/setTimeout #(react/dismiss-keyboard!) 100)))
    :accessibility-label :show-photo-icon}
   [icons/icon
    :main-icons/photo
    {:container-style {:margin 14 :margin-right 6}
     :color           (if images-showing? colors/blue colors/gray)}]])

(defn take-picture []
  (re-frame/dispatch
   [:request-permissions
    {:permissions [:camera]
     :on-allowed  #(re-frame/dispatch [:navigate-to :image-picker])
     :on-denied   (fn []
                    (utils/set-timeout
                     #(utils/show-popup (i18n/label :t/error)
                                        (i18n/label :t/camera-access-error))
                     50))}]))

(defn camera-button []
  [react/touchable-highlight {:on-press take-picture}
   [react/view {:style {:width 128 :height 208 :border-radius 4 :overflow :hidden}}
    [camera/camera {:style        {:flex 1}
                    :captureAudio false}
     camera-permissions-fn]]])

(defn buttons [camera-allowed?]
  [react/view
   [camera-button camera-allowed?]
   [react/touchable-highlight {:on-press #(re-frame/dispatch [:chat.ui/open-image-picker])}
    [react/view {:width       128 :height 48 :background-color "rgba(0, 0, 0, 0.86)" :border-radius 44
                 :align-items :center :justify-content :center :margin-top 8}
     [react/text {:style {:color colors/white}}
      "Photos"]]]])

(defn image-preview [uri first?]
  [react/touchable-highlight {:on-press #(re-frame/dispatch [:chat.ui/selected-image uri])}
   [react/image {:style  (merge {:width         128 :height 128
                                 :border-radius 4}
                                (when first?
                                  {:margin-bottom 8}))
                 :source {:uri uri}}]])

(defview photos []
  (letsubs [camera-roll-photos [:camera-roll-photos]]
    [react/view {:flex 1 :flex-direction :row}
     (for [[first-img second-img] (partition 2 camera-roll-photos)]
       [react/view {:margin-left 8}
        (when first-img
          [image-preview (-> first-img :node :image :uri) true])
        (when second-img
          [image-preview (-> second-img :node :image :uri) false])])]))

(defview image-view []
  (letsubs [bottom-anim-value (anim/create-value styles/image-panel-height)
            alpha-value       (anim/create-value 0)]
    {:component-did-mount (fn []
                            (show-panel-anim bottom-anim-value alpha-value)
                            (re-frame/dispatch [:chat.ui/camera-roll-get-photos 30]))}
    [react/animated-view {:style {:background-color :white
                                  :height           styles/image-panel-height
                                  :transform        [{:translateY bottom-anim-value}]
                                  :opacity          alpha-value}}
     [react/scroll-view {:horizontal true}
      [react/view {:flex 1 :flex-direction :row :margin-horizontal 8}
       [buttons]
       [photos]]]]))