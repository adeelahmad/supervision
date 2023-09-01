import argparse
import cv2
from tqdm import tqdm
from ultralytics import YOLO
import supervision as sv
import numpy as np


def process_video(
    source_weights_path: str,
    source_video_path: str,
    target_video_path: str = None,
    confidence_threshold: float = 0.3,
    iou_threshold: float = 0.7,
) -> None:
    model = YOLO(source_weights_path)
    tracker = sv.ByteTrack()
    box_annotator = sv.BoxAnnotator()
    frame_generator = sv.get_video_frames_generator(source_path=source_video_path)
    video_info = sv.VideoInfo.from_video_path(video_path=source_video_path)

    if target_video_path:
        with sv.VideoSink(target_path=target_video_path, video_info=video_info) as sink:
            for frame in tqdm(frame_generator, total=video_info.total_frames):
                annotated_frame = process_frame(
                    frame, model, tracker, box_annotator,
                    confidence_threshold, iou_threshold
                )
                sink.write_frame(frame=annotated_frame)
    else:
        for frame in tqdm(frame_generator, total=video_info.total_frames):
            annotated_frame = process_frame(
                frame, model, tracker, box_annotator,
                confidence_threshold, iou_threshold
            )
            cv2.imshow('Processed Video', annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()


def process_frame(
    frame: np.ndarray,
    model: YOLO,
    tracker: sv.ByteTrack,
    box_annotator: sv.BoxAnnotator,
    confidence_threshold: float,
    iou_threshold: float
) -> np.ndarray:
    results = model(
        frame, verbose=False, conf=confidence_threshold, iou=iou_threshold
    )[0]
    detections = sv.Detections.from_ultralytics(results)
    detections.class_id = np.zeros(len(detections))
    detections = tracker.update_with_detections(detections)
    labels = [
        f"#{tracker_id}"
        for _, _, confidence, class_id, tracker_id in detections
    ]
    return box_annotator.annotate(
        scene=frame.copy(),
        detections=detections,
        labels=labels)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Video Processing with YOLO and ByteTrack")

    parser.add_argument(
        "--source_weights_path", required=True,
        help="Path to the source weights file", type=str
    )
    parser.add_argument(
        "--source_video_path", required=True,
        help="Path to the source video file", type=str
    )
    parser.add_argument(
        "--target_video_path", default=None,
        help="Path to the target video file (output)", type=str
    )
    parser.add_argument(
        "--confidence_threshold", default=0.3,
        help="Confidence threshold for the model", type=float
    )
    parser.add_argument(
        "--iou_threshold", default=0.7,
        help="IOU threshold for the model", type=float
    )

    args = parser.parse_args()

    process_video(
        source_weights_path=args.source_weights_path,
        source_video_path=args.source_video_path,
        target_video_path=args.target_video_path,
        confidence_threshold=args.confidence_threshold,
        iou_threshold=args.iou_threshold,
    )