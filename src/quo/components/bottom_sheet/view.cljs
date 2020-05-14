(ns quo.components.bottom-sheet.view
  (:require [reagent.core :as reagent]
            [quo.react-native :as rn]
            [quo.react :as react]
            [quo.components.bottom-sheet.style :as styles]
            [quo.animated :as animated]
            [quo.gesture-handler :as gesture-handler]))

(def spring-config {:damping                   15
                    :mass                      1
                    :stiffness                 150
                    :overshootClamping         false
                    :restSpeedThreshold        0.1
                    :restDisplacementThreshold 0.1})

(def sheet-states {:undetermined 0
                   :open         3
                   :close        2})

(defn bottom-sheet []
  (let [content-height (reagent/atom 0)

        header-translation-y (animated/value 0)
        header-velocity-y    (animated/value (:undetermined gesture-handler/states))
        header-state         (animated/value (:undetermined gesture-handler/states))

        body-translation-y (animated/value 0)
        body-velocity-y    (animated/value (:undetermined gesture-handler/states))
        body-state         (animated/value (:undetermined gesture-handler/states))

        offset     (animated/value 0)
        body-ref   (react/create-ref)
        header-ref (react/create-ref)

        on-header-event (animated/event [{:nativeEvent
                                          {:translationY header-translation-y
                                           :state        header-state
                                           :velocityY    header-velocity-y}}]
                                        {:useNativeDriver true})

        on-body-event (animated/event [{:nativeEvent
                                        (if false ; inner scroll
                                          {:translationY body-translation-y
                                           :state        body-state
                                           :velocityY    body-velocity-y}
                                          {:translationY header-translation-y
                                           :state        header-state
                                           :velocityY    header-velocity-y})}])
        spring-offset (animated/with-spring-transition offset spring-config)
        close-sheet   (fn []
                        (animated/set-value offset 0))]
    (fn [{:keys [content on-cancel disable-drag? show-handle? visible
                 backdrop-dismiss? safe-area window-height back-button-cancel]
          :or  {show-handle?       true
                backdrop-dismiss?  true
                back-button-cancel true
                window-height      800}}]
      (let [height       (+ @content-height
                            styles/border-radius)
            max-height   (- window-height
                            (:top safe-area)
                            styles/margin-top)
            sheet-height (min max-height height)
            on-close     (fn []
                           (when on-cancel
                             (on-cancel)))
            translate-y  (animated/with-spring
                           {:value      (animated/divide header-translation-y 2)
                            :velocity   header-velocity-y
                            :offset     (animated/mix spring-offset 0 (- sheet-height))
                            :state      header-state
                            :config     spring-config
                            :snapPoints [(- sheet-height) 0]})
            opacity      (animated/interpolate translate-y
                                               {:inputRange  [(- sheet-height) 0]
                                                :outputRange [1 0]
                                                :extrapolate (:clamp animated/extrapolate)})]
        [:<>
         [animated/code {:exec (animated/block
                                [(animated/on-change translate-y
                                                     [(animated/cond* (animated/greater-or-eq translate-y 0)
                                                                      [(animated/call* [] on-close)])])
                                 (animated/on-change offset
                                                     [(animated/cond* (animated/and* (animated/not* offset)
                                                                                     (animated/greater-or-eq translate-y 0))
                                                                      [(animated/call* [] on-close)])])])}]
         [rn/modal {:visible                visible
                    :transparent            true
                    :status-bar-translucent true
                    :presentation-style     :overFullScreen
                    :hardware-accelerated   true
                    :on-show                #(animated/set-value offset 1)
                    :on-request-close       (fn []
                                              (when back-button-cancel
                                                (close-sheet)))}
          [rn/view {:style          styles/container
                    :pointer-events :box-none}
           [rn/touchable-without-feedback (merge {:style styles/container}
                                                 (when backdrop-dismiss?
                                                   {:on-press close-sheet}))
            [animated/view {:style (merge (styles/backdrop)
                                          {:opacity opacity})}]]
           [animated/view {:style (merge (styles/content-container window-height sheet-height)
                                         {:transform [{:translateY translate-y}
                                                      {:translateY (animated/add sheet-height window-height)}]})}
            [gesture-handler/pan-gesture-handler {:ref                  header-ref
                                                  :wait-for             body-ref
                                                  :enabled              (not disable-drag?)
                                                  :onGestureEvent       on-header-event
                                                  :onHandlerStateChange on-header-event}
             [animated/view  {:style styles/content-header}
              (when show-handle?
                [rn/view {:style styles/handle}])]]
            [gesture-handler/pan-gesture-handler {:ref                  body-ref
                                                  :wait-for             header-ref
                                                  :enabled              (not disable-drag?)
                                                  :onGestureEvent       on-body-event
                                                  :onHandlerStateChange on-body-event}
             [animated/view {:style     {:padding-top    styles/vertical-padding
                                         :padding-bottom (+ styles/vertical-padding
                                                            (:bottom safe-area))}
                             :on-layout #(->> ^js %
                                              .-nativeEvent
                                              .-layout
                                              .-height
                                              (reset! content-height))}
              [content]]]]]]]))))
