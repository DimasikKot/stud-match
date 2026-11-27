import type { StudentResponse } from "@/shared/api/students";
import { TextUI } from "@/shared/components/UI/TextUI";
import { IconUI } from "./UI/IconUI";

export const StudentCard = ({
  student,
  onClick,
}: {
  student: StudentResponse;
  onClick?: () => void;
}) => {
  return (
    <div
      onClick={onClick}
      className="flex flex-col justify-between pb-2 px-1 gap-1 overflow-clip
        transition-all duration-200 cursor-pointer
        bg-white border border-gray-300 hover:border-gray-400 hover:shadow-md"
    >
      <div className="flex flex-row justify-between gap-4">
        <div className="flex flex-1 min-w-0 max-h-12 flex-row items-center gap-2">
          <TextUI
            variant="title"
            title={student.fullname}
            className="-mt-1 line-clamp-1"
          >
            {student.fullname}
          </TextUI>
        </div>

        <IconUI name="person" className="text-gray-500" />
      </div>

      <div className="w-full flex-1 border-b border-gray-300" />

      <div className="flex justify-between -mb-1 gap-3 items-center">
        <TextUI variant="desc" className="flex-1 text-center">
          ID: {student.id}
        </TextUI>

        <IconUI name="chevron_right" className="text-gray-400" />
      </div>
    </div>
  );
};
