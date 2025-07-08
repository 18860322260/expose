def get_sum(nums, target):
    num_dict = {}

    # 遍历数组
    for i, num in enumerate(nums):

        complement = target - num

        if complement in num_dict:
            return [num_dict[complement], i]

        num_dict[num] = i

nums = [2, 7, 11, 15]
target = 9
print(get_sum(nums, target))