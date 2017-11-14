//#include <linux/kernel.h>
#include <linux/bio.h>
#include <linux/blkdev.h>
#include <linux/scatterlist.h>
#include "drbd_wrappers.h"

// Taken from blk-lib.c

struct bio_batch {
	atomic_t		done;
	unsigned long		flags;
	struct completion	*wait;
};

BIO_ENDIO_TYPE bio_batch_end_io BIO_ENDIO_ARGS(struct bio *bio)
{
	struct bio_batch *bb = bio->bi_private;

	BIO_ENDIO_FN_START;

	if (error && (error != -EOPNOTSUPP))
		clear_bit(BIO_UPTODATE, &bb->flags);
	if (atomic_dec_and_test(&bb->done))
		complete(bb->wait);
	bio_put(bio);

	BIO_ENDIO_FN_RETURN;
}

/**
 * blkdev_issue_zeroout - zero-fill a block range
 * @bdev:	blockdev to write
 * @sector:	start sector
 * @nr_sects:	number of sectors to write
 * @gfp_mask:	memory allocation flags (for bio_alloc)
 * @discard:    whether to discard the block range.
 *              IGNORED in this compat implementation.
 *
 * Description:
 *  Generate and issue number of bios with zerofiled pages.
 */
#warning "using compat implementation of blkdev_issue_zeroout"
int blkdev_issue_zeroout(struct block_device *bdev, sector_t sector,
			 sector_t nr_sects, gfp_t gfp_mask, /*IGNORED*/)
{
	int ret;
	struct bio *bio;
	struct bio_batch bb;
	unsigned int sz;
	struct page *page;
	DECLARE_COMPLETION_ONSTACK(wait);

	page = alloc_page(gfp_mask | __GFP_ZERO);
	if (!page)
		return -ENOMEM;

	atomic_set(&bb.done, 1);
	bb.flags = 1 << BIO_UPTODATE;
	bb.wait = &wait;

	ret = 0;
	while (nr_sects != 0) {
		bio = bio_alloc(gfp_mask,
				min(nr_sects, (sector_t)BIO_MAX_PAGES));
		if (!bio) {
			ret = -ENOMEM;
			break;
		}

		bio->bi_sector = sector;
		bio_set_dev(bio, bdev);
		bio->bi_end_io = bio_batch_end_io;
		bio->bi_private = &bb;

		while (nr_sects != 0) {
			sz = min((sector_t) PAGE_SIZE >> 9 , nr_sects);
			ret = bio_add_page(bio, page, sz << 9, 0);
			nr_sects -= ret >> 9;
			sector += ret >> 9;
			if (ret < (sz << 9))
				break;
		}
		ret = 0;
		atomic_inc(&bb.done);
		bio_set_op_attrs(bio, REQ_OP_WRITE, 0);
		submit_bio(bio);
	}

	/* Wait for bios in-flight */
	if (!atomic_dec_and_test(&bb.done))
		wait_for_completion(&wait);

	if (!test_bit(BIO_UPTODATE, &bb.flags))
		/* One of bios in the batch was completed with error.*/
		ret = -EIO;

	put_page(page);

	return ret;
}

